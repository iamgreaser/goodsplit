import logging
from pathlib import Path
from pathlib import PurePath
import sys
import time
from typing import Callable
from typing import Dict

from .reactor import Reactor

LOG = logging.getLogger("main")

from .games.system_shock_2 import SystemShock2Reactor
REACTORS: Dict[str, Callable[[Path], Reactor]] = {
    "system_shock_2": (lambda game_root: SystemShock2Reactor(root_dir=game_root)),
}


def main() -> None:
    if len(sys.argv[1:]) == 0:
        print(f"usage:")
        print(f"    {sys.argv[0]} game_name path/to/game/root")
        print(f"")
        print(f"supported game_name values:")
        for game_name in sorted(list(REACTORS.keys())):
            print(f"  - {game_name}")
        sys.exit(1)
        return

    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    game_name = sys.argv[1]
    game_root = Path(sys.argv[2]).expanduser().resolve()
    reactor = REACTORS[game_name](game_root)

    while True:
        reactor.update()
        time.sleep(0.001)

if __name__ == "__main__":
    main()
