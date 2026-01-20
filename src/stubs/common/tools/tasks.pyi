__license__ = "MIT"

from _typeshed import Incomplete

class Tasks:
    @staticmethod
    def blocking_status(
        prox: Incomplete,
        task_id: Incomplete,
        timeout: int = 300,
        polling_interval: int = 1,
    ) -> Incomplete: ...
    @staticmethod
    def decode_upid(upid: Incomplete) -> Incomplete: ...
    @staticmethod
    def decode_log(log_list: Incomplete) -> Incomplete: ...
