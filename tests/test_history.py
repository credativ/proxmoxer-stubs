import copy
from typing import Any

from stubgen.history import apply_history, compute_history


def schema(returns: dict[str, Any], path: str = "/thing") -> list[dict[str, Any]]:
    return [{"path": path, "text": path.strip("/"), "leaf": 1, "info": {"GET": {"method": "GET", "returns": returns}}}]


def item(**properties: Any) -> dict[str, Any]:
    return {"type": "array", "items": {"type": "object", "properties": properties}}


def relaxed(reference: list[dict[str, Any]], *snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    result = copy.deepcopy(reference)
    apply_history(result, compute_history(reference, list(snapshots)))
    props: dict[str, Any] = result[0]["info"]["GET"]["returns"]["items"]["properties"]
    return props


def test_required_since_first_snapshot() -> None:
    old = schema(item(id={"type": "string"}))
    new = schema(item(id={"type": "string"}, added={"type": "string"}))
    props = relaxed(new, old, new)
    assert not props["id"].get("optional")
    assert props["added"]["optional"] == 1


def test_optional_in_older_snapshot() -> None:
    old = schema(item(size={"type": "integer", "optional": 1}))
    new = schema(item(size={"type": "integer"}))
    assert relaxed(new, old, new)["size"]["optional"] == 1


def test_untyped_parent_in_older_snapshot() -> None:
    old = schema({"type": "array", "items": {"type": "object"}})
    new = schema(item(id={"type": "string"}))
    assert relaxed(new, old, new)["id"]["optional"] == 1


def test_new_endpoint_and_new_parent_keep_requiredness() -> None:
    new = schema(item(id={"type": "string"}, nested={"type": "object", "properties": {"x": {"type": "string"}}}))
    old_parent = schema(item(id={"type": "string"}))
    other_endpoint = schema(item(id={"type": "string"}), path="/other")
    props = relaxed(new, other_endpoint, old_parent, new)
    assert not props["id"].get("optional")
    assert props["nested"]["optional"] == 1
    assert not props["nested"]["properties"]["x"].get("optional")


def test_removed_enum_value_comes_back() -> None:
    old = schema(item(mode={"type": "string", "enum": ["auto", "none"]}))
    new = schema(item(mode={"type": "string", "enum": ["auto", "notify"]}))
    assert relaxed(new, old, new)["mode"]["enum"] == ["auto", "notify", "none"]


def test_removed_field_comes_back_as_optional() -> None:
    older = schema(item(id={"type": "string"}, maxfiles={"type": "integer", "description": "older"}))
    old = schema(item(id={"type": "string"}, maxfiles={"type": "integer", "description": "last"}))
    new = schema(item(id={"type": "string"}))
    history = compute_history(new, [older, old, new], labels=["9.0", "9.1", "9.2"])
    assert history["removed"]["GET /thing"][0]["last"] == "9.1"
    result = copy.deepcopy(new)
    assert apply_history(result, history).restored == 1
    props = result[0]["info"]["GET"]["returns"]["items"]["properties"]
    assert props["maxfiles"] == {"type": "integer", "description": "last", "optional": 1}
    assert not props["id"].get("optional")


def test_removed_field_of_reshaped_response_is_not_restored() -> None:
    old = schema(item(flags={"type": "string"}))
    new = schema({"type": "object", "properties": {"root": {"type": "object"}}})
    history = compute_history(new, [old, new])
    assert history["removed"] == {}


def test_type_change_is_recorded_but_not_applied() -> None:
    old = schema(item(host={"type": "boolean"}))
    new = schema(item(host={"type": "string"}))
    history = compute_history(new, [old, old, new], labels=["9.0", "9.1", "9.2"])
    assert history["types"]["GET /thing"] == [
        {"path": ["returns", "[]", "host"], "type": "string", "older": {'"boolean"': ["9.0", "9.1"]}}
    ]
    assert relaxed(new, old, new)["host"] == {"type": "string"}


def test_enum_unconstrained_in_older_snapshot_is_dropped() -> None:
    old = schema(item(level={"type": "string"}))
    new = schema(item(level={"type": "string", "enum": ["basic", "advanced"]}))
    props = relaxed(new, old, new)
    assert "enum" not in props["level"]
    assert props["level"]["type"] == "string"
