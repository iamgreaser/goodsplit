import logging
import math
from pathlib import Path
import sys
from typing import List

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

        # Game name
        self._game_name_label = tkinter.ttk.Label(
            self,
            text=f"{self._reactor.get_game_title()}",
        )
        self._game_name_label.grid(row=row, column=0, ipady=10)
        row += 1

        # Splits
        self._splits_frame = tkinter.ttk.Frame(
            self,
        )
        self._splits_frame.grid(
            row=row, column=0, ipady=10,
            sticky=tkinter.N+tkinter.S+tkinter.W+tkinter.E,
        )
        self.rowconfigure(index=row, weight=1)
        row += 1
        self._split_labels_name: List[tkinter.ttk.Label] = []
        self._split_labels_time: List[tkinter.ttk.Label] = []
        self._splits_frame.columnconfigure(index=0, weight=1)
        for i in range(self._split_row_count):
            self._split_labels_name.append(
                tkinter.ttk.Label(
                    self._splits_frame,
                    text=f"-",
                    width=20,
                )
            )
            self._split_labels_time.append(
                tkinter.ttk.Label(
                    self._splits_frame,
                    font="TkFixedFont",
                    text=f"--:--.-",
                )
            )
            self._splits_frame.rowconfigure(index=i, weight=1)
            self._split_labels_name[-1].grid(row=i, column=0, sticky=tkinter.W)
            self._split_labels_time[-1].grid(row=i, column=1, sticky=tkinter.E)

        # Stats
        self._stats_frame = tkinter.ttk.Frame(
            self,
        )
        self._stats_frame.grid(
            row=row, column=0, ipady=10,
            sticky=tkinter.N+tkinter.S+tkinter.W+tkinter.E,
        )
        row += 1

        statrow = 0
        self._stats_frame.columnconfigure(index=0, weight=1)
        self._stat_time_info_label = tkinter.ttk.Label(
            self._stats_frame,
            text="Time:",
        )
        self._stat_time_value_label = tkinter.ttk.Label(
            self._stats_frame,
            text="--:--:--.-",
        )
        self._stat_time_info_label.grid(row=statrow, column=0, sticky=tkinter.W)
        self._stat_time_value_label.grid(row=statrow, column=1, sticky=tkinter.E)
        self._stats_frame.rowconfigure(index=statrow, weight=1)
        statrow += 1

    def on_close(self) -> None:
        LOG.info(f"Closing window for {self._game_key}")
        self._is_dead = True
        try:
            self._reactor.cancel_run()
        except Exception as e:
            LOG.exception(e)
            # Otherwise let it through
        self.destroy() # type: ignore

    def on_tick(self) -> None:
        """Main update."""

        # Run update
        try:
            # Update reactor
            self._reactor.update()

            ordered_fuses = self._reactor.get_ordered_fuse_splits()
            for i, (ts, split_id,) in enumerate(ordered_fuses[-10:]):
                self._split_labels_name[i].configure(text=split_id.split(":")[-1])
                time_secs = ts[0]
                subsecs = int(math.floor(time_secs*10))
                subs = subsecs % 10
                secs = (subsecs // 10) % 60
                mins = (subsecs // 10) // 60
                time_str = f"{mins:02d}:{secs:02d}.{subs:01d}"
                self._split_labels_time[i].configure(text=time_str)

            for i in range(len(ordered_fuses)+1, self._split_row_count, 1):
                self._split_labels_time[i].configure(text="--:--.-")

            ts = self._reactor.fetch_time_now()
            if self._reactor.is_time_invalid():
                self._stat_time_value_label.configure(text="--:--:--.-")
            else:
                time_secs = ts[0]
                subsecs = int(math.floor(time_secs*10))
                subs = subsecs % 10
                secs = (subsecs // 10) % 60
                mins = ((subsecs // 10) // 60) % 60
                hours = ((subsecs // 10) // 60) // 60
                time_str = f"{hours:02d}:{mins:02d}:{secs:02d}.{subs:01d}"
                self._stat_time_value_label.configure(text=time_str)

        except Exception as e:
            LOG.exception(e)
            if not self._is_dead:
                # Call us after 500 msec because we screwed up
                self.after(500, self.on_tick)
        else:
            if not self._is_dead:
                # Call us after 1 msec
                self.after(1, self.on_tick)
