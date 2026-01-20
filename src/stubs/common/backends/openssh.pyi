__license__ = "MIT"

from _typeshed import Incomplete
from proxmoxer.backends.command_base import (
    CommandBaseBackend as CommandBaseBackend,
    CommandBaseSession as CommandBaseSession,
    shell_join as shell_join,
)

logger: Incomplete

class OpenSSHSession(CommandBaseSession):
    host: Incomplete
    user: Incomplete
    config_file: Incomplete
    port: Incomplete
    forward_ssh_agent: Incomplete
    identity_file: Incomplete
    ssh_client: Incomplete
    def __init__(
        self,
        host: Incomplete,
        user: Incomplete,
        config_file: Incomplete | None = None,
        port: int = 22,
        identity_file: Incomplete | None = None,
        forward_ssh_agent: bool = False,
        **kwargs: Incomplete
    ) -> None: ...
    def upload_file_obj(
        self, file_obj: Incomplete, remote_path: Incomplete
    ) -> None: ...

class Backend(CommandBaseBackend):
    session: Incomplete
    target: Incomplete
    def __init__(self, *args: Incomplete, **kwargs: Incomplete) -> None: ...
