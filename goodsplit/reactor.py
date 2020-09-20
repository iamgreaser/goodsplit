from abc import ABCMeta
from abc import abstractmethod
import logging
import math
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import sqlite3

from .db import DB
from .interface import Event
from .interface import EventSource
from .interface import TimeBase

LOG = logging.getLogger("reactor")


class Reactor:
    """The thing that takes care of all the stuff and things."""
    __slots__ = (
        "_active_game_id",
        "_active_run_id",
        "_active_time_base_ids",
        "_db",
        "_event_sources",
        "_fuse_splits",
        "_is_stopped",
        "_last_time_str",
        "_ordered_fuse_splits",
        "_sql_conn",
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
        self._ordered_fuse_splits: List[Tuple[List[float], str]] = []
        self._time_load_start: Optional[List[float]] = None

        self._db = DB()

        self._active_game_id = self._db.ensure_game_id(
            game_key=self.get_game_key(),
            game_title=self.get_game_title(),
        )
        self._active_time_base_ids = [
            self._db.ensure_time_base_id(
                game_id=self._active_game_id,
                type_key=tb.get_time_base_key(),
            )
            for tb in time_bases
        ]
        self._active_run_id: Optional[int] = None

    @classmethod
    @abstractmethod
    def get_game_title(cls) -> str:
        """Gets the title of this game."""
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_game_key(cls) -> str:
        """Gets the unique identifier of this game."""
        raise NotImplementedError()

    def get_ordered_fuse_splits(self) -> List[Tuple[List[float], str]]:
        """
        Gets an ordered list of the current activated fuse splits.

        Returns a list of ([ts0, ...], split_id,).
        """
        return list(map(
            (lambda t: (list(t[0]), t[1],)),
            self._ordered_fuse_splits,
        ))

    def is_time_invalid(self) -> bool:
        """Is the time invalid?"""
        return self._time_invalid

    def fetch_time_now(self) -> List[float]:
        """Fetch all time now."""
        time_now = [tb.fetch_time() for tb in self._time_bases]
        return time_now

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
        self._active_run_id = self._db.create_run_id(
            game_id=self._active_game_id,
        )
        self._time_load_start = None
        self._is_stopped = False
        self._time_invalid = False

        self._fuse_splits = {}
        self._ordered_fuse_splits = []

        for tb in self._time_bases:
            tb.reset_to_zero()

        self.do_fuse_split(
            ts=[tb.fetch_time() for tb in self._time_bases],
            split_id="$system:start",
        )

        LOG.info("Run started!")

    def finish_run(self) -> None:
        """Finishes a successful run."""
        if not self._is_stopped:
            self.do_fuse_split(
                ts=[tb.fetch_time() for tb in self._time_bases],
                split_id="$system:finish",
            )
        self._time_load_start = None
        self._is_stopped = True
        self._active_run_id = None
        LOG.info("Run finished!")

    def cancel_run(self) -> None:
        """Cancels the current run."""
        if not self._is_stopped:
            self.do_fuse_split(
                ts=[tb.fetch_time() for tb in self._time_bases],
                split_id="$system:cancel",
            )
        for tb in self._time_bases:
            tb.reset_to_zero()
        self._time_load_start = None
        self._is_stopped = True
        self._time_invalid = True
        self._active_run_id = None
        self._fuse_splits = {}
        self._ordered_fuse_splits = []
        LOG.info("Run cancelled.")

    def do_fuse_split(self, ts: List[float], split_id: str) -> None:
        """Adds a fuse split if we haven't blown the fuse already."""
        if self._active_run_id is None:
            LOG.warn(f"Attempted to add a fuse split {split_id!r} when no run available!")
            return
        if split_id in self._fuse_splits:
            return

        # Blow the fuse and make a split!
        self._fuse_splits[split_id] = list(ts)
        self._ordered_fuse_splits.append((list(ts), split_id,))
        LOG.info(f"Fuse split {self.convert_times_to_str(ts)}: {split_id!r}")
        fuse_split_type_id = self._db.ensure_fuse_split_type(
            game_id=self._active_game_id,
            type_key=split_id,
        )
        split_db_id = self._db.create_split_id(
            run_id=self._active_run_id,
            fuse_split_type_id=fuse_split_type_id,
        )
        for secs, time_base_id in zip(ts, self._active_time_base_ids):
            value_microseconds = int(math.floor(secs*1000000))
            time_stamp_id = self._db.create_time_stamp_id(
                split_id=split_db_id,
                time_base_id=time_base_id,
                value_microseconds=value_microseconds,
            )

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
