import enum
import logging
from pathlib import Path
from pathlib import PurePath
from typing import List

from goodsplit.interface import Event
from goodsplit.reactor import Reactor
from goodsplit.sources.inotify import INotifyEventSource
from goodsplit.sources.inotify import OpenFileEvent
from goodsplit.sources.inotify import CloseFileEvent
from goodsplit.time_base import MonotonicFloatSeconds

LOG = logging.getLogger("system_shock_2")


class RunState(enum.Enum):
    """
    The current state of the run.

    STOPPED = Not started
    STOPPED_AWAITING_EARTH_MIS = Waiting for earth.mis to load
    RUNNING = Running the game
    FINISHED = Finished the game
    """
    STOPPED = enum.auto()
    STOPPED_AWAITING_EARTH_MIS = enum.auto()
    RUNNING = enum.auto()
    FINISHED = enum.auto()


class SystemShock2Reactor(Reactor):
    """A reactor for System Shock 2 runs."""
    __slots__ = (
        "_path_cs1_avi",
        "_path_cs3_avi",
        "_path_earth_mis",
        "_path_ss2_exe",
        "_root_dir",
        "_run_state",
        "_missions_entered",
    )

    def __init__(self, *, root_dir: Path) -> None:
        # Set up paths
        self._root_dir = root_dir.resolve()
        self._path_cs1_avi = self._root_dir / "Data" / "cutscenes" / "cs1.avi"
        self._path_cs3_avi = self._root_dir / "Data" / "cutscenes" / "Cs3.avi"
        self._path_earth_mis = self._root_dir / "Data" / "earth.mis"
        self._path_ss2_exe = self._root_dir / "ss2.exe"

        self._run_state = RunState.STOPPED

        super().__init__(
            event_sources=[
                INotifyEventSource(fpaths=[
                    # Start, stop, split
                    self._root_dir / "Data",
                    self._root_dir / "Data" / "cutscenes",

                    # Crash monitoring
                    self._root_dir / "ss2.exe",
                ]),
            ],
            time_bases = [
                MonotonicFloatSeconds(),
            ],
        )

    def on_event(self, ts: List[float], ev: Event) -> None:
        time_str = self.convert_times_to_str(ts)

        if isinstance(ev, OpenFileEvent):
            if ev.fpath == self._path_cs1_avi:
                # Open cs1.avi: Opening cutscene. We're about to start a run.
                self.cancel_run()
                self._run_state = RunState.STOPPED_AWAITING_EARTH_MIS
                LOG.info(f"{time_str} Watching cs1.avi, previous run has been cancelled")

            elif ev.fpath == self._path_cs3_avi:
                # Open cs3.avi: Ending cutscene. Run is (probably) finished.
                self.finish_run()
                self._run_state = RunState.FINISHED
                LOG.info(f"{time_str} Watching cs3.avi, run is over!")

            elif ev.fpath.name.lower().endswith(".avi"):
                # Some cutscene.
                #LOG.info(f"{time_str} TODO: Cutscene open {ev}")
                self.do_fuse_split(ts, f"cutscene:{ev.fpath.name.lower()}")

            elif ev.fpath == self._path_earth_mis:
                # earth.mis is special.
                LOG.info(f"{time_str} Loading earth.mis... run starts when it gets closed")

            elif ev.fpath.name.lower().endswith(".mis"):
                # Some mission.
                #LOG.info(f"{time_str} Splitting on {ev.fpath.name.lower()}")
                self.do_fuse_split(ts, f"mission:{ev.fpath.name.lower()}")
                self.start_loading(ts)

            elif ev.fpath.name.lower() in ["shock2.gam", "allobjs.osm", "motiondb.bin"]:
                # Some files we don't care about.
                pass

            else:
                LOG.info(f"{time_str} TODO: {ev}")

        elif isinstance(ev, CloseFileEvent):
            if ev.fpath == self._path_earth_mis:
                # Close earth.mis: If we're waiting for this, then start the run!
                if self._run_state == RunState.STOPPED_AWAITING_EARTH_MIS:
                    self._run_state = RunState.RUNNING
                    self.start_run()

            elif ev.fpath.name.lower().endswith(".mis"):
                # Some mission.
                #LOG.info(f"{time_str} TODO: Mission close {ev} (for load removal)")
                self.stop_loading(ts)

            elif ev.fpath.name.lower().endswith(".avi"):
                # Some cutscene.
                # We really don't care when these close.
                pass

            elif ev.fpath.name.lower() in ["shock2.gam", "allobjs.osm", "motiondb.bin"]:
                # Some files we don't care about.
                pass

            else:
                LOG.info(f"{time_str} TODO: {ev}")
