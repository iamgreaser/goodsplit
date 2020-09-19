import time

from .interface import TimeBase


class UnixTimeFloatSeconds(TimeBase):
    __slots__ = ()

    def __init__(self) -> None:
        pass

    def fetch_time(self) -> float:
        return time.time()

    def reset_to_zero(self) -> None:
        # Not supported.
        pass


class MonotonicFloatSeconds(TimeBase):
    __slots__ = (
        "_last_zero_time",
    )

    def __init__(self) -> None:
        self.reset_to_zero()

    def fetch_time(self) -> float:
        return self.fetch_time_unzeroed() - self._last_zero_time

    def fetch_time_unzeroed(self) -> float:
        return time.monotonic()

    def reset_to_zero(self) -> None:
        self._last_zero_time = self.fetch_time_unzeroed()
