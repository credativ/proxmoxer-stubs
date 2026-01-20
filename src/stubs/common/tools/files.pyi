__license__ = "MIT"

from _typeshed import Incomplete
from enum import Enum
from ..core import (
    ProxmoxResource as ProxmoxResource,
    ResourceException as ResourceException,
)
from .tasks import Tasks as Tasks

CHECKSUM_CHUNK_SIZE: int
logger: Incomplete

class ChecksumInfo:
    name: Incomplete
    hex_size: Incomplete
    def __init__(self, name: str, hex_size: int) -> None: ...

class SupportedChecksums(Enum):
    SHA512 = ...
    SHA256 = ...
    SHA224 = ...
    SHA384 = ...
    MD5 = ...
    SHA1 = ...

class Files:
    def __init__(self, prox: ProxmoxResource, node: str, storage: str) -> None: ...
    def upload_local_file_to_storage(
        self,
        filename: str,
        do_checksum_check: bool = True,
        blocking_status: bool = True,
    ) -> Incomplete: ...
    def download_file_to_storage(
        self,
        url: str,
        checksum: str | None = None,
        checksum_type: str | None = None,
        blocking_status: bool = True,
    ) -> Incomplete: ...
    def get_file_info(self, url: str) -> Incomplete: ...
    @staticmethod
    def get_checksums_from_file_url(
        url: str, filename: str | None = None, preferred_type: Incomplete = ...
    ) -> Incomplete: ...
