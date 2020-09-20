import logging
from pathlib import Path
from pathlib import PurePath
import sys
import time
from typing import Callable
from typing import Dict

from .reactor import Reactor
from .games import REACTOR_CONSTRUCTORS
from .games import REACTORS
from .gui_tk.root import TkGuiRoot

LOG = logging.getLogger("main")


def print_usage() -> None:
    print(f"usage:")
    print(f"    {sys.argv[0]} game_name path/to/game/root")
    print(f"")
    print(f"supported game_name values:")
    for game_key in sorted(list(REACTORS.keys())):
        game_cls = REACTORS[game_key]
        print(f"  - {game_key}: {game_cls.get_game_title()}")

def main() -> None:
    if False and len(sys.argv[1:]) == 0:
        print_usage()
        sys.exit(1)
        return

    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    if True:
        TkGuiRoot(args=sys.argv[1:]).run()
    else:
        game_name = sys.argv[1]
        game_root = Path(sys.argv[2]).expanduser().resolve()
        reactor = REACTOR_CONSTRUCTORS[game_name](game_root)

        while True:
            reactor.update()
            time.sleep(0.001)

if __name__ == "__main__":
    main()
