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

def rrddata() -> None:
    # The API documentation declares an rrddata row as an object without any
    # properties; the data sources are patched in from pve-cluster
    # src/pmxcfs/status.c. They differ between nodes, guests and storages, and
    # every one of them is optional because PVE::RRD::create_rrd_data() omits
    # the ones whose value is NaN.
    import proxmoxer_types.v8 as proxmoxer8
    import proxmoxer_types.v9 as proxmoxer9

    node = proxmoxer9.ProxmoxAPI().nodes('node').rrddata.get()[0]
    vm = proxmoxer9.ProxmoxAPI().nodes('node').qemu(42).rrddata.get()[0]
    ct = proxmoxer9.ProxmoxAPI().nodes('node').lxc(42).rrddata.get()[0]
    storage = proxmoxer9.ProxmoxAPI().nodes('node').storage('storage').rrddata.get()[0]

    assert_type(node, proxmoxer9.core.ProxmoxAPI.Nodes.Node.Rrddata._Get.TypedDict)
    assert_type(vm, proxmoxer9.core.ProxmoxAPI.Nodes.Node.Qemu.Vmid.Rrddata._Get.TypedDict)
    assert_type(ct, proxmoxer9.core.ProxmoxAPI.Nodes.Node.Lxc.Vmid.Rrddata._Get.TypedDict)
    assert_type(storage, proxmoxer9.core.ProxmoxAPI.Nodes.Node.Storage.Storage.Rrddata._Get.TypedDict)

    # Known fields: the timestamp is the only one every row is guaranteed to
    # carry, all data sources are optional.
    assert_type(node['time'], int)
    assert_type(vm['time'], int)
    assert_type(storage['time'], int)

    assert_type(node.get('loadavg'), Optional[float])
    assert_type(node.get('memavailable'), Optional[float])
    assert_type(vm.get('diskread'), Optional[float])
    assert_type(ct.get('memhost'), Optional[float])
    assert_type(storage.get('total'), Optional[float])
    assert_type(storage.get('used'), Optional[float])

    assert 'cpu' in node
    assert_type(node['cpu'], float)

    # Pressure fields, present since pve-cluster 9.0.3
    assert_type(node.get('pressurecpusome'), Optional[float])
    assert_type(node.get('pressureiosome'), Optional[float])
    assert_type(node.get('pressureiofull'), Optional[float])
    assert_type(node.get('pressurememorysome'), Optional[float])
    assert_type(node.get('pressurememoryfull'), Optional[float])
    assert_type(vm.get('pressurecpufull'), Optional[float])
    assert_type(ct.get('pressurecpufull'), Optional[float])

    # Unknown fields. Every ignore below asserts that the access is rejected:
    # mypy runs in strict mode, so an ignore that turns out to be unnecessary
    # fails the run.
    node['pressureiosom']  # type: ignore[typeddict-item]

    # There are no pressuredisk* data sources, they are called pressureio*
    node['pressuredisksome']  # type: ignore[typeddict-item]
    node['pressurediskfull']  # type: ignore[typeddict-item]
    vm['pressuredisksome']  # type: ignore[typeddict-item]
    vm['pressurediskfull']  # type: ignore[typeddict-item]

    # Nodes, unlike guests, have no cpu pressure full data source
    node['pressurecpufull']  # type: ignore[typeddict-item]

    # Fields of one resource kind do not exist for the others
    vm['loadavg']  # type: ignore[typeddict-item]
    vm['arcsize']  # type: ignore[typeddict-item]
    ct['iowait']  # type: ignore[typeddict-item]
    node['diskread']  # type: ignore[typeddict-item]
    node['memhost']  # type: ignore[typeddict-item]
    storage['cpu']  # type: ignore[typeddict-item]

    # Older API versions are left untyped
    assert_type(proxmoxer8.ProxmoxAPI().nodes('node').rrddata.get(), list[dict[str, Any]])


def test_cache() -> None:
    from proxmoxer_types.v9 import ProxmoxAPI
    api = ProxmoxAPI(backend="local")

    assert api.nodes is api.nodes
    assert api.nodes("foo") is api.nodes("foo")
    assert api.nodes("foo").get is api.nodes("foo").get

    assert api.nodes("foo") is not api.nodes("bar")
    assert api.nodes("foo").get is not api.nodes("bar").get
