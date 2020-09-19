from abc import ABCMeta
import logging
from pathlib import Path
from pathlib import PurePath
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import inotify_simple # type: ignore
from inotify_simple import flags as inotify_flags

from ..interface import Event
from ..interface import EventSource

LOG = logging.getLogger("inotify")


class INotifyEvent(Event, metaclass=ABCMeta):
    """An abstract event based on the Linux inotify interface."""
    __slots__ = (
        "fpath",
    )

    def __init__(self, *, fpath: PurePath) -> None:
        self.fpath: PurePath = fpath

    def __eq__(self, other: Any) -> bool:
        if other.__class__ == self.__class__:
            if other.fpath == self.fpath:
                return True

        return False


class OpenFileEvent(INotifyEvent):
    """A file was opened."""
    __slots__ = ()

class CloseFileEvent(INotifyEvent):
    """A file was closed."""
    __slots__ = ()

class CloseWriteableFileEvent(CloseFileEvent):
    """A writeable file was closed."""
    __slots__ = ()

class CloseUnwriteableFileEvent(CloseFileEvent):
    """An unwriteable file was closed."""
    __slots__ = ()


class INotifyEventSource(EventSource):
    """An event source based on the Linux inotify interface."""
    __slots__ = (
        "_fpaths",
        "_fpath_by_id",
        "_inotify",
    )

    def __init__(self, fpaths: List[PurePath]) -> None:
        self._fpaths = list(fpaths)
        self._fpath_by_id: Dict[int, Path] = {}
        self._inotify = inotify_simple.INotify()
        for fpath in self._fpaths:
            LOG.info(f"Resolving {fpath!r}")
            real_path = Path(fpath).resolve(strict=True)
            LOG.info(f"Watching {real_path!r}")
            watch_id = self._inotify.add_watch(str(real_path),
                (0
                    | inotify_flags.OPEN
                    | inotify_flags.CLOSE_NOWRITE
                    ),
            )
            LOG.debug(f"Watch ID = {watch_id!r}")
            self._fpath_by_id[watch_id] = real_path

    # Implementation
    def pull_events(self) -> List[Event]:
        events: List[Event] = []

        # wd, mask, cookie, name
        raw_events: List[Tuple[int, int, int, str]] = list(self._inotify.read(timeout=0))
        for raw_event in raw_events:
            wd, mask, cookie, name = raw_event
            
            # Ignore directory reads for now --GM
            if (mask & inotify_flags.ISDIR) != 0:
                continue

            path = self._fpath_by_id[wd] / name
            LOG.debug(f"ev: {mask:08X} {cookie:08X} {path!r}")

            if (mask & inotify_flags.OPEN) != 0:
                events.append(OpenFileEvent(fpath=path))
            if (mask & inotify_flags.CLOSE_WRITE) != 0:
                events.append(CloseWriteableFileEvent(fpath=path))
            if (mask & inotify_flags.CLOSE_NOWRITE) != 0:
                events.append(CloseUnwriteableFileEvent(fpath=path))
                
        return events
