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
replication.py:6: note: Revealed type is "TypedDict('proxmoxer_types.v9.core.ProxmoxAPI.Cluster.Replication.Id._Get.TypedDict', {'comment'?: builtins.str, 'digest'?: builtins.str, 'disable'?: builtins.bool, 'guest': builtins.int, 'id': builtins.str, 'jobnum': builtins.int, 'rate'?: builtins.float, 'remove_job'?: builtins.str, 'schedule'?: builtins.str, 'source'?: builtins.str, 'target': builtins.str, 'type': builtins.str})"
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
