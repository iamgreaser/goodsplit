from abc import ABCMeta
from abc import abstractmethod
from typing import Generic
from typing import List
from typing import Optional
from typing import cast


class Event(metaclass=ABCMeta):
    """Something that happened."""
    __slots__ = ()

    def __repr__(self) -> str:
        arg_strings = [
            f"{sn}={getattr(self,sn)!r}"
            for sn in self.__class__.__init__.__code__.co_varnames[1:]
        ]
        arg_list_str = ", ".join(arg_strings)
        return f"{self.__class__.__name__}({arg_list_str})"


class EventSource(metaclass=ABCMeta):
    """A source of events."""
    __slots__ = ()

    @abstractmethod
    def pull_events(self) -> List[Event]:
        """Pulls a sequence of events."""
        raise NotImplementedError()


class TimeBase(metaclass=ABCMeta):
    """A way of keeping time."""
    __slots__ = ()

    @abstractmethod
    def fetch_time(self) -> float:
        """Gets the time of right now."""
        raise NotImplementedError()

    @abstractmethod
    def reset_to_zero(self) -> None:
        """Resets this timer to zero."""
