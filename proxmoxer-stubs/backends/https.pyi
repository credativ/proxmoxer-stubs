__license__ = "MIT"

import io
import requests
from _typeshed import Incomplete
from ..core import (
    AuthenticationError as AuthenticationError,
    SERVICES as SERVICES,
    config_failure as config_failure,
)
from requests.auth import AuthBase

logger: Incomplete
STREAMING_SIZE_THRESHOLD: Incomplete
SSL_OVERFLOW_THRESHOLD: int

class ProxmoxHTTPAuthBase(AuthBase):
    def __call__(self, req: Incomplete) -> Incomplete: ...
    def get_cookies(self) -> Incomplete: ...
    def get_tokens(self) -> Incomplete: ...
    timeout: Incomplete
    service: Incomplete
    verify_ssl: Incomplete
    cert: Incomplete
    def __init__(
        self,
        timeout: int = 5,
        service: str = "PVE",
        verify_ssl: bool = False,
        cert: Incomplete | None = None,
    ) -> None: ...

class ProxmoxHTTPAuth(ProxmoxHTTPAuthBase):
    renew_age: int
    base_url: Incomplete
    username: Incomplete
    pve_auth_ticket: str
    def __init__(
        self,
        username: Incomplete,
        password: Incomplete,
        otp: Incomplete | None = None,
        base_url: str = "",
        **kwargs: Incomplete
    ) -> None: ...
    def get_cookies(self) -> Incomplete: ...
    def get_tokens(self) -> Incomplete: ...
    def __call__(self, req: Incomplete) -> Incomplete: ...

class ProxmoxHTTPApiTokenAuth(ProxmoxHTTPAuthBase):
    username: Incomplete
    token_name: Incomplete
    token_value: Incomplete
    def __init__(
        self,
        username: Incomplete,
        token_name: Incomplete,
        token_value: Incomplete,
        **kwargs: Incomplete
    ) -> None: ...
    def __call__(self, req: Incomplete) -> Incomplete: ...

class JsonSerializer:
    content_types: Incomplete
    def get_accept_types(self) -> Incomplete: ...
    def loads(self, response: Incomplete) -> Incomplete: ...
    def loads_errors(self, response: Incomplete) -> Incomplete: ...

class ProxmoxHttpSession(requests.Session):
    def request(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        method: Incomplete,
        url: Incomplete,
        params: Incomplete | None = None,
        data: Incomplete | None = None,
        headers: Incomplete | None = None,
        cookies: Incomplete | None = None,
        files: Incomplete | None = None,
        auth: Incomplete | None = None,
        timeout: Incomplete | None = None,
        allow_redirects: bool = True,
        proxies: Incomplete | None = None,
        hooks: Incomplete | None = None,
        stream: Incomplete | None = None,
        verify: Incomplete | None = None,
        cert: Incomplete | None = None,
        serializer: Incomplete | None = None,
    ) -> Incomplete: ...

class Backend:
    proxies: Incomplete
    cert: Incomplete
    mode: Incomplete
    base_url: Incomplete
    auth: Incomplete
    def __init__(
        self,
        host: Incomplete,
        user: Incomplete | None = None,
        password: Incomplete | None = None,
        otp: Incomplete | None = None,
        port: Incomplete | None = None,
        verify_ssl: bool = True,
        mode: str = "json",
        timeout: int = 5,
        token_name: Incomplete | None = None,
        token_value: Incomplete | None = None,
        path_prefix: Incomplete | None = None,
        service: str = "PVE",
        cert: Incomplete | None = None,
    ) -> None: ...
    def get_session(self) -> Incomplete: ...
    def get_base_url(self) -> Incomplete: ...
    def get_serializer(self) -> Incomplete: ...
    def get_tokens(self) -> Incomplete: ...

def get_file_size(file_obj: io.BufferedRandom) -> int: ...
def get_file_size_partial(file_obj: io.BufferedRandom) -> int: ...
