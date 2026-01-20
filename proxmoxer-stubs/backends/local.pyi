__license__ = "MIT"

from _typeshed import Incomplete
from proxmoxer.backends.command_base import (
    CommandBaseBackend as CommandBaseBackend,
    CommandBaseSession as CommandBaseSession,
)

class LocalSession(CommandBaseSession):
    def upload_file_obj(
        self, file_obj: Incomplete, remote_path: Incomplete
    ) -> None: ...

class Backend(CommandBaseBackend):
    session: Incomplete
    target: str
    def __init__(self, *args: Incomplete, **kwargs: Incomplete) -> None: ...
