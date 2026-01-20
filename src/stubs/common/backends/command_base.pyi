__license__ = "MIT"

from _typeshed import Incomplete
from ..core import SERVICES as SERVICES

logger: Incomplete

def shell_join(args: Incomplete) -> Incomplete: ...

class Response:
    status_code: Incomplete
    content: Incomplete
    text: Incomplete
    headers: Incomplete
    def __init__(self, content: Incomplete, status_code: Incomplete) -> None: ...

class CommandBaseSession:
    service: Incomplete
    timeout: Incomplete
    sudo: Incomplete
    def __init__(
        self, service: str = "PVE", timeout: int = 5, sudo: bool = False
    ) -> None: ...
    def request(
        self,
        method: Incomplete,
        url: Incomplete,
        data: Incomplete | None = None,
        params: Incomplete | None = None,
        headers: Incomplete | None = None,
    ) -> Incomplete: ...
    def upload_file_obj(
        self, file_obj: Incomplete, remote_path: Incomplete
    ) -> None: ...

class JsonSimpleSerializer:
    def loads(self, response: Incomplete) -> Incomplete: ...
    def loads_errors(self, response: Incomplete) -> Incomplete: ...

class CommandBaseBackend:
    session: Incomplete
    target: Incomplete
    def __init__(self) -> None: ...
    def get_session(self) -> Incomplete: ...
    def get_base_url(self) -> Incomplete: ...
    def get_serializer(self) -> Incomplete: ...
