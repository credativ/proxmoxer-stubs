import pytest

from proxmoxer_types.v9.core import ProxmoxAPI


@pytest.mark.parametrize("flag", [1, True])
def test_model_accepts_numeric_and_json_booleans(flag: int | bool) -> None:
    # jobs.cfg booleans are sent as 0/1 (PVE::SectionConfig), while e.g. the Ceph
    # service flags are JSON booleans since pve-manager 9.1.18 and 0/1 before
    job = ProxmoxAPI.Cluster.Backup.Id._Get.Model.model_validate({"enabled": flag})
    assert job.enabled is True
    mds = ProxmoxAPI.Nodes.Node.Ceph.Mds._Get.Model.model_validate(
        {"name": "a", "state": "up:active", "direxists": flag, "service": flag, "standby_replay": flag}
    )
    assert mds.direxists is True
    assert mds.service is True
    assert mds.standby_replay is True
