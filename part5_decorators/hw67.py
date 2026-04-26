import json
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
INVALID_TRIGGERS_ON = "triggers_on must be an exception type!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        self._validate_args(critical_count, time_to_recover, triggers_on)
        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

    @staticmethod
    def _get_name[**P, R_co](func: CallableWithMeta[P, R_co]) -> str:
        return f"{func.__module__}.{func.__name__}"

    @staticmethod
    def _validate_args(
        critical_count: int, time_to_recover: int, triggers_on: type[Exception]
    ) -> None:
        errors: list[Exception] = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if not isinstance(triggers_on, type) or not issubclass(triggers_on, Exception):
            errors.append(TypeError(INVALID_TRIGGERS_ON))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        fail_count: int = 0
        blocked_at: datetime | None = None
        func_name = self._get_name(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            nonlocal fail_count, blocked_at

            self._raise_if_blocked(blocked_at, func_name)
            blocked_at = None
            try:
                result: R_co = func(*args, **kwargs)
            except self.triggers_on as err:
                fail_count += 1
                if fail_count >= self.critical_count:
                    blocked_at = datetime.now(UTC)
                    raise BreakerError(func_name, blocked_at) from err
                raise

            fail_count = 0
            return result

        return wrapper

    def _raise_if_blocked(self, blocked_at: datetime | None, func_name: str) -> None:
        if blocked_at is None:
            return
        expires_at = blocked_at + timedelta(seconds=self.time_to_recover)
        if datetime.now(UTC) < expires_at:
            raise BreakerError(func_name, blocked_at)


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
