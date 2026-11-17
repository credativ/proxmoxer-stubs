"""Defensive return types across the minor releases of a major version.

A schema snapshot describes one point release, but a `proxmoxer_types.v*`
module covers a whole major version. This module compares the reference
(newest) schema with the schema snapshots of a release range and records what
older servers of the same major version may still return:

- required: the return fields that are required in every snapshot. When
  generating code, required fields that are not listed here become optional.
- enums: enum values that older snapshots list but the reference does not
  (they are added back), and enums that some snapshot does not constrain at
  all (they become plain strings).
- removed: return fields that older snapshots document but the reference does
  not. They are added back as optional fields.
- types: return fields whose documented type differs in older snapshots. They
  are only reported, see below.

Rules for a field that is required in the reference schema:

- Snapshots that do not have the endpoint at all are ignored: calling the
  endpoint fails on those servers anyway.
- If the field is optional in any snapshot, it is not required.
- If the field is missing in a snapshot although its parent object is typed
  there, the field is new and not required.
- If the field is missing because its parent is untyped in a snapshot (an
  object without properties, an array without items), nothing was promised
  and the field is not required.
- If the field is missing because one of its ancestor properties is new, the
  snapshot is ignored for this field: the ancestor is optional itself, and the
  field stays required relative to it.

Rules for a field with an enum in the reference schema, over the snapshots
that have the field:

- Values listed by any snapshot are kept.
- If a snapshot has the field without an enum, the enum is dropped.

Rules for a field that a snapshot documents but the reference does not:

- It is added back, optional, with its definition from the last snapshot that
  documents it, if its parent still exists in the reference as an object with
  properties.
- Otherwise the response changed shape, and the field is not added back; a
  patch has to decide how to annotate it.

Type changes are recorded under "types" but not applied. A changed type
in the documentation is usually a correction of a wrong declaration, and a
union of old and new types would carry the error forward. Each type change
needs a review of the server code: where the server output really changed, a
patch has to annotate both forms. Changes of the server output that the
documentation never reflected cannot be detected here at all.

These rules only widen return types. They must not be applied to request
parameters: a value or parameter that only some releases accept is not safe to
send to every server of the major version.

Field paths are lists of segments starting with "returns". A segment is a
property name, "[]" for array items or "{}" for additionalProperties.

Usage (maintainers, when updating apidata):

    python3 -m stubgen.history --pve-docs ../pve-docs --since <commit> \\
        --reference apidata/apidata-v9.json --output apidata/history-v9.json

(or `make history-v9 PVE_DOCS=../pve-docs`)
"""

import argparse
import copy
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

__all__ = ["compute_history", "apply_history"]

ITEMS = "[]"
ADDITIONAL = "{}"

FieldPath = tuple[str, ...]


@dataclass
class Node:
    typed: bool  # object with properties, or array with items
    is_property: bool
    optional: bool
    schema: dict[str, Any]


def _walk_returns(schema: Any, prefix: FieldPath) -> Iterator[tuple[FieldPath, Node]]:
    if not isinstance(schema, dict):
        yield prefix, Node(typed=False, is_property=False, optional=False, schema={})
        return
    props = schema.get("properties")
    items = schema.get("items")
    additional = schema.get("additionalProperties")
    typed = isinstance(props, dict) or isinstance(items, dict) or isinstance(additional, dict)
    yield prefix, Node(typed=typed, is_property=False, optional=False, schema=schema)
    if isinstance(props, dict):
        for name, sub in props.items():
            assert name not in (ITEMS, ADDITIONAL), f"ambiguous property name {name!r} at {prefix}"
            path = (*prefix, name)
            for child_path, node in _walk_returns(sub, path):
                if child_path == path:
                    node.is_property = True
                    node.optional = bool(isinstance(sub, dict) and sub.get("optional"))
                yield child_path, node
    if isinstance(items, dict):
        yield from _walk_returns(items, (*prefix, ITEMS))
    if isinstance(additional, dict):
        yield from _walk_returns(additional, (*prefix, ADDITIONAL))


def _endpoints(schema: list[dict[str, Any]]) -> Iterator[tuple[str, dict[str, Any]]]:
    for item in schema:
        for method, info in (item.get("info") or {}).items():
            yield f"{method} {item['path']}", info
        yield from _endpoints(item.get("children") or [])


Index = dict[str, dict[FieldPath, Node]]


def _index(schema: list[dict[str, Any]]) -> Index:
    return {
        endpoint: dict(_walk_returns(info.get("returns"), ("returns",)))
        for endpoint, info in _endpoints(schema)
    }


def _required_in(field: FieldPath, nodes: dict[FieldPath, Node]) -> bool | None:
    """True/False if the snapshot keeps/breaks requiredness of field, None if it does not constrain it."""
    if field in nodes:
        return not nodes[field].optional
    depth = len(field) - 1
    while field[:depth] not in nodes:
        depth -= 1
    ancestor, missing = nodes[field[:depth]], field[depth]
    if depth < len(field) - 1 and missing not in (ITEMS, ADDITIONAL) and ancestor.typed:
        # an ancestor property is new; it is optional itself
        return None
    return False


def _enum(node: Node) -> list[str] | None:
    enum = node.schema.get("enum")
    return [str(value) for value in enum] if isinstance(enum, list) and enum else None


def _has_properties(node: Node | None) -> bool:
    return node is not None and isinstance(node.schema.get("properties"), dict)


def compute_history(
    reference: list[dict[str, Any]],
    snapshots: list[list[dict[str, Any]]],
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Compare reference with snapshots, ordered from oldest to newest, optionally labeled by release."""
    ref = _index(reference)
    indexes = [_index(snapshot) for snapshot in snapshots]

    required: dict[str, list[list[str]]] = {}
    enums: dict[str, list[dict[str, Any]]] = {}
    removed: dict[str, list[dict[str, Any]]] = {}
    types: dict[str, list[dict[str, Any]]] = {}
    for endpoint, nodes in ref.items():
        others = [index[endpoint] for index in indexes if endpoint in index]

        last: dict[FieldPath, tuple[int, Node]] = {}
        for number, index in enumerate(indexes):
            for path, node in index.get(endpoint, {}).items():
                if node.is_property and path not in nodes and _has_properties(nodes.get(path[:-1])):
                    last[path] = (number, node)
        if last:
            entries = []
            for path, (number, node) in sorted(last.items()):
                definition = copy.deepcopy(node.schema)
                definition["optional"] = 1
                entry: dict[str, Any] = {"path": list(path), "schema": definition}
                if labels:
                    entry["last"] = labels[number]
                entries.append(entry)
            removed[endpoint] = entries

        fields = [
            list(path)
            for path, node in nodes.items()
            if node.is_property
            and not node.optional
            and all(_required_in(path, other) is not False for other in others)
        ]
        if fields:
            required[endpoint] = sorted(fields)

        changes: list[dict[str, Any]] = []
        for path, node in nodes.items():
            if (current := _enum(node)) is None:
                continue
            seen = [other[path] for other in others if path in other]
            if any(_enum(old) is None for old in seen):
                changes.append({"path": list(path), "open": True})
                continue
            extra = sorted({value for old in seen for value in _enum(old) or []} - set(current))
            if extra:
                changes.append({"path": list(path), "add": extra})
        if changes:
            enums[endpoint] = sorted(changes, key=lambda change: change["path"])

        retyped: list[dict[str, Any]] = []
        for path, node in nodes.items():
            if (current := node.schema.get("type")) is None:
                continue
            older: dict[str, list[str]] = {}
            for number, index in enumerate(indexes):
                old = index.get(endpoint, {}).get(path)
                if old is not None and (previous := old.schema.get("type")) is not None and previous != current:
                    versions = older.setdefault(json.dumps(previous), [])
                    if labels and labels[number] not in versions:
                        versions.append(labels[number])
            if older:
                retyped.append({"path": list(path), "type": current, "older": older})
        if retyped:
            types[endpoint] = retyped

    return {
        "required": dict(sorted(required.items())),
        "enums": dict(sorted(enums.items())),
        "removed": dict(sorted(removed.items())),
        "types": dict(sorted(types.items())),
    }


@dataclass
class Applied:
    optional: int = 0
    enum_values: int = 0
    enum_opened: int = 0
    restored: int = 0


def apply_history(schema: list[dict[str, Any]], history: dict[str, Any]) -> Applied:
    """Relax the return types of schema in place according to history."""
    applied = Applied()
    required: dict[str, list[list[str]]] = history["required"]
    enums: dict[str, list[dict[str, Any]]] = history["enums"]
    for endpoint, info in _endpoints(schema):
        nodes = dict(_walk_returns(info.get("returns"), ("returns",)))

        allowed = {tuple(path) for path in required.get(endpoint, [])}
        for path, node in nodes.items():
            if node.is_property and not node.optional and path not in allowed:
                node.schema["optional"] = 1
                applied.optional += 1

        for change in enums.get(endpoint, []):
            target = nodes.get(tuple(change["path"]))
            if target is None or (current := _enum(target)) is None:
                continue
            if change.get("open"):
                del target.schema["enum"]
                applied.enum_opened += 1
            else:
                extra = [value for value in change["add"] if value not in current]
                target.schema["enum"] = [*target.schema["enum"], *extra]
                applied.enum_values += len(extra)

        # after the required fields: restored fields keep their nested requiredness
        for entry in history.get("removed", {}).get(endpoint, []):
            *parent, name = entry["path"]
            container = nodes.get(tuple(parent))
            if container is None or not _has_properties(container):
                continue
            properties = container.schema["properties"]
            if name not in properties:
                properties[name] = copy.deepcopy(entry["schema"])
                applied.restored += 1
    return applied


def _git(pve_docs: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(pve_docs), *args], check=True, capture_output=True, text=True
    ).stdout


def _load_apidata_js(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    prefix = "const apiSchema = "
    assert text.startswith(prefix), "unexpected apidata.js format"
    data: list[dict[str, Any]] = json.loads(text[len(prefix):].rstrip(";").strip())
    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record what older releases may return, from the pve-docs schema snapshots of a range.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--pve-docs", type=Path, required=True, help="clone of git://git.proxmox.com/git/pve-docs.git")
    parser.add_argument("--since", required=True, help="first pve-docs commit of the range (inclusive)")
    parser.add_argument("--until", default="HEAD", help="last pve-docs revision of the range (inclusive)")
    parser.add_argument("--reference", type=Path, required=True, help="JSON schema the history is computed for")
    parser.add_argument("--output", type=Path, required=True, help="history destination")
    args = parser.parse_args()

    apidata = "api-viewer/apidata.js"
    commits = _git(args.pve_docs, "rev-list", "--reverse", f"{args.since}^..{args.until}", "--", apidata).split()
    assert commits, "no snapshots in range"
    snapshots: list[list[dict[str, Any]]] = []
    sources: list[dict[str, str]] = []
    for commit in commits:
        snapshots.append(_load_apidata_js(_git(args.pve_docs, "show", f"{commit}:{apidata}")))
        version = _git(args.pve_docs, "show", f"{commit}:debian/changelog").split("\n", 1)[0].split("(")[1].split(")")[0]
        date = _git(args.pve_docs, "log", "-1", "--format=%ad", "--date=short", commit).strip()
        sources.append({"commit": commit, "date": date, "pve-docs": version})

    with args.reference.open() as src:
        reference = json.load(src)
    history = compute_history(reference, snapshots, labels=[source["pve-docs"] for source in sources])
    with args.output.open("w") as dst:
        json.dump({"snapshots": sources, **history}, dst, indent=1)
        print(file=dst)
    required = sum(len(fields) for fields in history["required"].values())
    enums = sum(len(changes) for changes in history["enums"].values())
    removed = sum(len(entries) for entries in history["removed"].values())
    print(
        f"{len(commits)} snapshots: {required} required return fields, {enums} enum changes, "
        f"{removed} removed fields in {args.output}"
    )
    if history["types"]:
        print("Type changes (not applied; review each, and patch where the server output changed):")
        for endpoint, entries in history["types"].items():
            for entry in entries:
                older = ", ".join(f"{previous} in {', '.join(versions)}" for previous, versions in entry["older"].items())
                print(f"  {endpoint} {'.'.join(entry['path'][1:])}: {json.dumps(entry['type'])}, was {older}")


if __name__ == "__main__":
    main()
