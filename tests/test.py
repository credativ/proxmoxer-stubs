from typing import Any, Literal, Optional, assert_type, TYPE_CHECKING

def typechecks() -> None:
    import proxmoxer
    import proxmoxer_types.v6 as proxmoxer6
    import proxmoxer_types.v7 as proxmoxer7
    import proxmoxer_types.v8 as proxmoxer8
    import proxmoxer_types.v9 as proxmoxer9

    assert_type(proxmoxer6.ProxmoxAPI().cluster.ceph.metadata.get(), dict[Any, Any])
    assert_type(proxmoxer6.ProxmoxAPI().cluster.ceph.metadata.get()["mon"], Any)
    assert_type(proxmoxer6.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], Any)

    assert_type(proxmoxer7.ProxmoxAPI().cluster.ceph.metadata.get(), proxmoxer7.core.ProxmoxAPI.Cluster.Ceph.Metadata._Get.TypedDict)
    assert_type(proxmoxer7.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], str)
    assert_type(proxmoxer7.ProxmoxAPI().cluster.ha.status.current.get()[42]["type"], Any)

    assert_type(proxmoxer8.ProxmoxAPI().cluster.ceph.metadata.get(), proxmoxer8.core.ProxmoxAPI.Cluster.Ceph.Metadata._Get.TypedDict)
    assert_type(proxmoxer8.ProxmoxAPI().cluster.ceph.metadata.get()["mon"]["{id}"]["ceph_version"], str)
    assert_type(proxmoxer8.ProxmoxAPI().cluster.ha.status.current.get()[42]["type"], dict[Any, Any])
    assert_type(proxmoxer8.ProxmoxAPI().cluster.replication("some-id").get(), dict[Any, Any])

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


def models() -> None:
    import proxmoxer
    assert_type(proxmoxer.ProxmoxAPI().cluster.ceph.metadata.get.model().mon.id.ceph_version, str)
    assert_type(proxmoxer.ProxmoxAPI().cluster.replication("some-id").get.model().jobnum, int)
    assert_type(proxmoxer.ProxmoxAPI().cluster.firewall.groups("foo")(42).get.model().log, Optional[Literal['emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug', 'nolog']])


def aliases() -> None:
    import proxmoxer
    assert_type(proxmoxer.ProxmoxAPI().cluster.config.nodes("node").post()["warnings"], list[str])
    assert_type(proxmoxer.ProxmoxAPI().cluster.config.nodes("node").create()["warnings"], list[str])

    assert_type(proxmoxer.ProxmoxAPI().storage("storage").put()["type"], Literal['btrfs', 'cephfs', 'cifs', 'dir', 'esxi', 'iscsi', 'iscsidirect', 'lvm', 'lvmthin', 'nfs', 'pbs', 'rbd', 'zfs', 'zfspool'])
    assert_type(proxmoxer.ProxmoxAPI().storage("storage").set()["type"], Literal['btrfs', 'cephfs', 'cifs', 'dir', 'esxi', 'iscsi', 'iscsidirect', 'lvm', 'lvmthin', 'nfs', 'pbs', 'rbd', 'zfs', 'zfspool'])
