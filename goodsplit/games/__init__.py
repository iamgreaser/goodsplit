from pathlib import Path
from typing import Callable
from typing import Dict
from typing import Type

from ..reactor import Reactor
from .system_shock_2 import SystemShock2Reactor as _SystemShock2Reactor


REACTOR_CONSTRUCTORS: Dict[str, Callable[[Path, Path], Reactor]] = {
    "system_shock_2": (lambda game_root_dir, game_user_dir: _SystemShock2Reactor(root_dir=game_root_dir)),
}
REACTORS: Dict[str, Type[Reactor]] = {
    "system_shock_2": _SystemShock2Reactor,
}
