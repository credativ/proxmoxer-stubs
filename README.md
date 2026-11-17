# proxmoxer-stubs

Type annotations for data obtained by `proxmoxer.ProxmoxAPI` calls.

## Usage

### Annotations only

```python
import typing
import proxmoxer

api = proxmoxer.ProxmoxAPI()

typing.reveal_type(api.cluster.replication("some-id").get())
```

```
replication.py:6: note: Revealed type is "TypedDict(proxmoxer_types.v9.core.ProxmoxAPI.Cluster.Replication.Id._Get.TypedDict, {'comment'?: str, 'digest'?: str, 'disable'?: Literal[0] | Literal[1] | bool, 'guest'?: int, 'id'?: str, 'jobnum'?: int, 'rate'?: float, 'remove_job'?: Literal['local'] | Literal['full'], 'schedule'?: str, 'skip-freeze-fs'?: Literal[0] | Literal[1] | bool, 'source'?: str, 'target'?: str, 'type'?: Literal['local']})"
Success: no issues found in 1 source file
```

```
reveal_type(proxmoxer.ProxmoxAPI().cluster.firewall.groups("foo")(42).get().get("log"))
```

```
log.py:4: note: Revealed type is "Literal['emerg'] | Literal['alert'] | Literal['crit'] | Literal['err'] | Literal['warning'] | Literal['notice'] | Literal['info'] | Literal['debug'] | Literal['nolog'] | None"
Success: no issues found in 1 source file
```

For a legacy REST-API:

```
import typing

if typing.TYPE_CHECKING:
    import proxmoxer_types.v8 as proxmoxer
else:
    import proxmoxer

api = proxmoxer.ProxmoxAPI()

typing.reveal_type(api.cluster.replication("some-id").get())
```

```
legacy.py:10: note: Revealed type is "builtins.dict[builtins.str, Any]"
Success: no issues found in 1 source file
```

#### Dependencies

- For type checking: `proxmoxer-stubs`, `pydantic`
- At runtime: None

### Wrapper mode

Example from [proxmoxer](https://github.com/proxmoxer/proxmoxer):

```
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI(
    "proxmox_host", user="admin@pam", password="secret_word", verify_ssl=False
)

for node in proxmox.nodes.get():
    for vm in proxmox.nodes(node["node"]).qemu.get():
        print(f"{vm['vmid']}. {vm['name']} => {vm['status']}")
```

The above works the same in wrapper mode:

```
from proxmoxer_types.v9 import ProxmoxAPI

proxmox = ProxmoxAPI(
    "proxmox_host", user="admin@pam", password="secret_word", verify_ssl=False
)

for node in proxmox.nodes.get():
    for vm in proxmox.nodes(node["node"]).qemu.get():
        print(f"{vm['vmid']}. {vm['name']} => {vm['status']}")
```

The returned objects in both above cases are built-in types, possibly nested in
`list` or `dict`. Working with those may be inconvenient, as optional
`dict` keys may not exist at all. For convenience the following is possible:

```
for node in proxmox.nodes.get.model():
    for vm in proxmox.nodes(node.node).qemu.get.model():
        print(f"{vm.vmid}. {vm.name} => {vm.status}")
```

Whenever a `method(...)` call - `method` being `get`, `post`, `put`, `delete`,
`set` or `create` - returns a structure that is or contains a
`TypedDict`-annotated `dict`, `method.model(...)` returns a
`pydantic.BaseModel` instead.

Values of optional fields are possibly `None` in the model instance.

#### Additional dependencies

- For type checking: `proxmoxer-stubs`, `pydantic`
- At runtime: `proxmoxer-stubs`, `pydantic`

## Caveats

### Minor releases

Each `proxmoxer_types.v*` module covers a whole major release and is generated
from the schema of its newest minor release. Endpoints, parameters and enum
values added in later minor releases are annotated even though older servers
of the same major release do not support them.

For v9, return types are relaxed so they hold for every release since 9.0,
according to the documented schema of each release (see
`apidata/history-v9.json`):

- A return field is only annotated as required (and validated as such by
  `method.model(...)`) if every release marks it as required. A field that was
  added or documented later is `NotRequired` in the `TypedDict` and `Optional`
  in the model.
- An enum contains the values of all releases, including values that newer
  releases no longer list. An enum that some release does not constrain at all
  is annotated as `str`.
- A return field that older releases document but newer ones do not is kept as
  an optional field.

A changed type in the documentation is usually a correction and is not merged.
Where the server output itself changed, a patch has to cover both forms.
Output changes that the documentation never reflected can only be found by
reviewing the PVE source.

### Booleans

PVE documents many return fields as boolean, but its Perl handlers send `0`/`1`
unless they explicitly return JSON booleans; values read from configuration
files are always sent as numbers. Documented booleans are therefore annotated as
`proxmoxer_types.PveBool`, an alias of `Literal[0, 1] | bool`, in the
`TypedDict`. Truth tests and `== True` work on both; use `method.model(...)`
for actual `bool` values.

```python
from proxmoxer_types import PveBool

def is_enabled(flag: PveBool | None) -> bool:
    return flag is None or bool(flag)
```

### Endpoint notation

`proxmoxer.ProxmoxAPI` has several ways of expressing the same endpoint due to its magic implementation.

```
>>> api.cluster.replication("some-id")
ProxmoxResource (/cluster/replication/some-id)
>>>
>>> api("cluster/replication/some-id")
ProxmoxResource (/cluster/replication/some-id)
>>>
>>> api("cluster")("replication")("some-id")
ProxmoxResource (/cluster/replication/some-id)
```

Only the first form will produce useful typing insights.

Parameters to `get`, `post`, `put`, `delete`, `set`, `create` are currently not individually annotated.

The [API documentation](https://pve.proxmox.com/pve-docs/api-viewer/) is
occasionally wrong or incomplete. In wrapper mode, `pydantic` will `raise` a
`ValidationError` if the documentation is wrong.
