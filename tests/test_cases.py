from typing import Any, Literal, Optional, assert_type, TYPE_CHECKING

def typechecks() -> None:
    import proxmoxer
    import proxmoxer_types.v6 as proxmoxer6
    import proxmoxer_types.v7 as proxmoxer7
    import proxmoxer_types.v8 as proxmoxer8
    import proxmoxer_types.v9 as proxmoxer9

    assert_type(proxmoxer6.ProxmoxAPI().cluster.ceph.metadata.get(), dict[str, Any])
    assert_type(proxmoxer6.ProxmoxAPI().cluster.ceph.metadata.get()["mon"], Any)
    assert_type(proxmoxer6.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], Any)

    assert_type(proxmoxer7.ProxmoxAPI().cluster.ceph.metadata.get(), proxmoxer7.core.ProxmoxAPI.Cluster.Ceph.Metadata._Get.TypedDict)
    assert_type(proxmoxer7.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], str)
    assert_type(proxmoxer7.ProxmoxAPI().cluster.ha.status.current.get()[42]["type"], Any)

    assert_type(proxmoxer8.ProxmoxAPI().cluster.ceph.metadata.get(), proxmoxer8.core.ProxmoxAPI.Cluster.Ceph.Metadata._Get.TypedDict)
    assert_type(proxmoxer8.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], str)
    assert_type(proxmoxer8.ProxmoxAPI().cluster.ha.status.current.get()[42]["type"], dict[str, Any])
    assert_type(proxmoxer8.ProxmoxAPI().cluster.replication("some-id").get(), dict[str, Any])

    assert_type(proxmoxer9.ProxmoxAPI().cluster.ceph.metadata.get(), proxmoxer9.core.ProxmoxAPI.Cluster.Ceph.Metadata._Get.TypedDict)
    assert_type(proxmoxer9.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], str)
    assert_type(proxmoxer9.ProxmoxAPI().cluster.ha.status.current.get()[42]["type"], Literal['quorum', 'master', 'lrm', 'service'])
    assert_type(proxmoxer9.ProxmoxAPI().cluster.replication("some-id").get(), proxmoxer9.core.ProxmoxAPI.Cluster.Replication.Id._Get.TypedDict)
    assert_type(proxmoxer9.ProxmoxAPI().cluster.replication("some-id").get()["jobnum"], int)

    assert_type(proxmoxer.ProxmoxAPI().cluster.ceph.metadata.get(), proxmoxer9.core.ProxmoxAPI.Cluster.Ceph.Metadata._Get.TypedDict)
    assert_type(proxmoxer.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], str)
    assert_type(proxmoxer.ProxmoxAPI().cluster.ha.status.current.get()[42]["type"], Literal['quorum', 'master', 'lrm', 'service'])
    assert_type(proxmoxer.ProxmoxAPI().cluster.replication("some-id").get(), proxmoxer9.core.ProxmoxAPI.Cluster.Replication.Id._Get.TypedDict)
    assert_type(proxmoxer.ProxmoxAPI().cluster.replication("some-id").get()["jobnum"], int)

    assert_type(proxmoxer.ProxmoxAPI().cluster.firewall.groups("foo")(42).get().get("log"), Optional[Literal['emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug', 'nolog']])

    storage = proxmoxer.ProxmoxAPI().nodes('42').storage.get()[0]
    assert 'active' in storage
    assert 'enabled' in storage
    assert_type(storage['active'], Literal[0, 1])
    assert_type(storage['enabled'], Literal[0, 1])

def models() -> None:
    import proxmoxer
    assert_type(proxmoxer.ProxmoxAPI().cluster.ceph.metadata.get.model().mon.id.ceph_version, str)
    assert_type(proxmoxer.ProxmoxAPI().cluster.replication("some-id").get.model().jobnum, int)
    assert_type(proxmoxer.ProxmoxAPI().cluster.firewall.groups("foo")(42).get.model().log, Optional[Literal['emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug', 'nolog']])

    storage = proxmoxer.ProxmoxAPI().nodes('42').storage.get.model()[0]
    assert storage.active is not None
    assert storage.enabled is not None
    assert_type(storage.active, bool)
    assert_type(storage.enabled, bool)

def aliases() -> None:
    import proxmoxer
    assert_type(proxmoxer.ProxmoxAPI().cluster.config.nodes("node").post()["warnings"], list[str])
    assert_type(proxmoxer.ProxmoxAPI().cluster.config.nodes("node").create()["warnings"], list[str])

    assert_type(proxmoxer.ProxmoxAPI().storage("storage").put()["type"], Literal['btrfs', 'cephfs', 'cifs', 'dir', 'esxi', 'iscsi', 'iscsidirect', 'lvm', 'lvmthin', 'nfs', 'pbs', 'rbd', 'zfs', 'zfspool'])
    assert_type(proxmoxer.ProxmoxAPI().storage("storage").set()["type"], Literal['btrfs', 'cephfs', 'cifs', 'dir', 'esxi', 'iscsi', 'iscsidirect', 'lvm', 'lvmthin', 'nfs', 'pbs', 'rbd', 'zfs', 'zfspool'])

def test_cache() -> None:
    from proxmoxer_types.v9 import ProxmoxAPI
    api = ProxmoxAPI(backend="local")

    assert api.nodes is api.nodes
    assert api.nodes("foo") is api.nodes("foo")
    assert api.nodes("foo").get is api.nodes("foo").get

    assert api.nodes("foo") is not api.nodes("bar")
    assert api.nodes("foo").get is not api.nodes("bar").get
