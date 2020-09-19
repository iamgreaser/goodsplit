from abc import ABCMeta
from abc import abstractmethod
import logging
import math
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .interface import Event
from .interface import EventSource
from .interface import TimeBase

LOG = logging.getLogger("reactor")


class Reactor:
    """The thing that takes care of all the stuff and things."""
    __slots__ = (
        "_event_sources",
        "_fuse_splits",
        "_is_stopped",
        "_last_time_str",
        "_time_bases",
        "_time_invalid",
        "_time_load_start",
    )

    def __init__(self, time_bases: List[TimeBase], event_sources: List[EventSource]) -> None:
        self._time_bases = list(time_bases)
        self._event_sources = list(event_sources)
        self._is_stopped = True
        self._time_invalid = True
        self._last_time_str: str = "--TODO-SET-TIME--"
        self._fuse_splits: Dict[str, List[float]] = {}
        self._time_load_start: Optional[List[float]] = None

    def update(self) -> None:
        """Updates the reactor."""
        time_now = [tb.fetch_time() for tb in self._time_bases]
        events = []
        time_str = self.convert_times_to_str(time_now)
        for src in self._event_sources:
            events += src.pull_events()

        for ev in events:
            self.on_event(time_now, ev)
            if self._time_invalid:
                LOG.debug(f"{time_str}: {ev}")
            else:
                if (not self._is_stopped):
                    self._last_time_str = time_str
                LOG.debug(f"{self._last_time_str}: {ev}")

    @abstractmethod
    def on_event(self, ts: List[float], ev: Event) -> None:
        """Processes the given event."""
        raise NotImplementedError()

    def convert_times_to_str(self, ts: List[float]) -> str:
        """Convert a group of times to a nice string."""
        time_str = "[" + ("|".join(map(self.convert_time_to_str, ts))) + "]"
        return time_str

    def convert_time_to_str(self, t: float) -> str:
        """Convert a given time to a nice string."""

        if self._time_invalid:
            return "--:--:--.------"
        else:
            ft = int(math.floor(t))
            h = ft // 60 // 60
            m = (ft // 60) % 60
            s = ft % 60
            sub = int(math.floor((t - float(ft)) * 1000000))
            return f"{h:02d}:{m:02d}:{s:02d}.{sub:06d}"

    def start_run(self) -> None:
        """Starts a new run."""
        for tb in self._time_bases:
            tb.reset_to_zero()
        self._time_load_start = None
        self._is_stopped = False
        self._time_invalid = False
        LOG.info("Run started!")

    def finish_run(self) -> None:
        """Finishes a successful run."""
        self._time_load_start = None
        self._is_stopped = True
        LOG.info("Run finished!")

    def cancel_run(self) -> None:
        """Cancels the current run."""
        for tb in self._time_bases:
            tb.reset_to_zero()
        self._time_load_start = None
        self._is_stopped = True
        self._time_invalid = True
        LOG.info("Run cancelled.")

    def do_fuse_split(self, ts: List[float], split_id: str) -> None:
        """Adds a fuse split if we haven't blown the fuse already."""
        if split_id in self._fuse_splits:
            return

        # Blow the fuse and make a split!
        self._fuse_splits[split_id] = list(ts)
        LOG.info(f"Fuse split {self.convert_times_to_str(ts)}: {split_id!r}")

    def start_loading(self, ts: List[float]) -> None:
        """Start a loading period for load removal."""
        if self._time_load_start is None:
            self._time_load_start = list(ts)

    def stop_loading(self, ts: List[float]) -> None:
        """Stops a loading period and applies load removal."""
        if self._time_load_start is not None:
            load_beg = self._time_load_start
            load_end = list(ts)
            loads_to_remove = [e-b for b, e in zip(load_beg, load_end)]
            LOG.info(f"Load removal to apply: {loads_to_remove}")
            self._time_load_start = None
