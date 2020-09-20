import logging
from pathlib import Path
import sys

import tkinter
import tkinter.font # type: ignore
import tkinter.ttk

from goodsplit.db import DB
from goodsplit.games import REACTOR_CONSTRUCTORS
from goodsplit.reactor import Reactor

LOG = logging.getLogger("tk_game")


class TkGameWindow(tkinter.Toplevel):
    """A game window."""
    def __init__(self, *, game_key: str, game_root_dir: str, game_user_dir: str) -> None:
        super().__init__()
        self.configure(background="#000000")
        self._is_dead = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._game_key = game_key
        self._game_root_dir = Path(game_root_dir)
        self._game_user_dir = Path(game_user_dir)
        LOG.info(f"Creating game reactor")
        self._reactor: Reactor = REACTOR_CONSTRUCTORS[game_key](
            self._game_root_dir,
            self._game_user_dir,
        )
        self.title(f"GS: {self._reactor.get_game_title()}")
        self._init_fonts()
        self._init_widgets()
        self.after_idle(self.on_tick) # type: ignore

    def is_dead(self) -> bool:
        """Is this window dead?"""
        return self._is_dead

    def _init_fonts(self) -> None:
        """Initialises all the fonts used."""
        pass

    def _init_widgets(self) -> None:
        """Initialises all the widgets in this window."""
        self.grid()
        self.columnconfigure(index=0, weight=1)

        self._split_row_count = 10

        row = 0

        # TODO!
        self._todo_label = tkinter.ttk.Label(
            self,
            text="TODO: Put splits here.\n\nIn the meantime, your runs ARE being recorded.",
        )
        self._todo_label.grid(row=row, column=0)
        self.rowconfigure(index=row, weight=1)
        row += 1

    def on_close(self) -> None:
        LOG.info(f"Closing window for {self._game_key}")
        self._is_dead = True
        self._reactor.cancel_run()
        self.destroy() # type: ignore

    def on_tick(self) -> None:
        """Main update."""

        # Run update
        try:
            # Update reactor
            self._reactor.update()

        except Exception as e:
            LOG.exception(e)
            if not self._is_dead:
                # Call us after 500 msec because we screwed up
                self.after(500, self.on_tick)
        else:
            if not self._is_dead:
                # Call us after 1 msec
                self.after(1, self.on_tick)
