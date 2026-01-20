# proxmoxer-stubs

Type annotations for data obtained by `proxmoxer.ProxmoxAPI` calls.

## Usage

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
legacy.py:10: note: Revealed type is "builtins.dict[Any, Any]"
Success: no issues found in 1 source file
```

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

Parameters to `get`, `post`, `put`, `delete` are currently not individually annotated.
