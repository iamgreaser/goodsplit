import logging
from pathlib import Path
import sys
from typing import Any
from typing import List
from typing import Sequence
from typing import Set

import tkinter
import tkinter.filedialog
import tkinter.font # type: ignore
import tkinter.messagebox
import tkinter.ttk

from goodsplit.db import DB
from goodsplit.games import REACTOR_CONSTRUCTORS
from goodsplit.games import REACTORS
from goodsplit.reactor import Reactor

from .game import TkGameWindow

LOG = logging.getLogger("tk_root")


class TkGuiRoot(tkinter.Tk):
    """The Tk application root."""
    def __init__(self, *, args: Sequence[str]) -> None:
        super().__init__()
        self.title("Game Setup - Goodsplit")
        self._db = DB()
        self._init_fonts()
        self._init_widgets()
        self._active_windows: List[tkinter.Toplevel] = []

    def run(self) -> None:
        """Runs the main loop."""
        self.mainloop()

    def _init_fonts(self) -> None:
        """Initialises all the fonts used."""
        families_set: Set[str]
        families_set = set(tkinter.font.families())
        families_set_lower = set(f.lower() for f in families_set)
        sans_family=(list(filter(lambda f: f in families_set, [
            "DejaVu Sans",
            "Bitstream Vera Sans",
            "Verdana", # Gee, guess where they got the name of that font from
            "Helvetica",
            "",
        ])))[0]
        mono_family=(list(filter(lambda f: f.lower() in families_set_lower, [
            "DejaVu Sans Mono",
            "Bitstream Vera Sans Mono",
            "Lucida Console",
            "Courier New",
            "Courier",
            "",
        ])))[0]

        self.font_size = 12

        self.font_default = tkinter.font.nametofont("TkDefaultFont")
        self.font_default.configure(
            family=sans_family,
            size=self.font_size,
        )

        self.font_entry = tkinter.font.nametofont("TkTextFont")
        self.font_entry.configure(
            family=mono_family,
            size=self.font_size,
        )

    def _init_widgets(self) -> None:
        """Initialises all the widgets in the root window."""
        self.grid()
        self.columnconfigure(index=0, weight=0)
        self.columnconfigure(index=1, weight=1)
        self.columnconfigure(index=2, weight=0)

        row = 0

        # Game Select
        self._game_sel_var = tkinter.StringVar()
        self._game_sel_options = [
            g.get_game_key()
            for g in sorted(
                list(REACTORS.values()),
                key=(lambda g: g.get_game_title().lower()),
            )
        ]
        self._game_sel_label = tkinter.ttk.Label(
            self,
            text="Game select:",
        )
        self._game_sel_box = tkinter.ttk.Combobox(
            self,
            textvariable=self._game_sel_var,
            values=self._game_sel_options,
            width=40,
        )
        self._game_sel_box.bind(
            "<<ComboboxSelected>>",
            self.on_game_select,
        )
        self._game_sel_label.grid(row=row, column=0, sticky=tkinter.E)
        self._game_sel_box.grid(row=row, column=1, sticky=tkinter.W+tkinter.E)
        row += 1

        # Game root dir
        self._game_root_dir_var = tkinter.StringVar()
        self._game_root_dir_label = tkinter.ttk.Label(
            self,
            text="Game root dir:",
        )
        self._game_root_dir_entry = tkinter.ttk.Entry(
            self,
            textvariable=self._game_root_dir_var,
            validate="focusout",
            validatecommand=self.on_game_root_dir_change,
        )
        self._game_root_dir_button = tkinter.ttk.Button(
            self,
            text="Find",
            command=self.on_game_root_dir_button,
        )
        self._game_root_dir_label.grid(row=row, column=0, sticky=tkinter.E)
        self._game_root_dir_entry.grid(row=row, column=1, sticky=tkinter.W+tkinter.E)
        self._game_root_dir_button.grid(row=row, column=2, sticky=tkinter.W+tkinter.E)
        row += 1

        # Game user dir
        self._game_user_dir_var = tkinter.StringVar()
        self._game_user_dir_label = tkinter.ttk.Label(
            self,
            text="Game user dir:",
        )
        self._game_user_dir_entry = tkinter.ttk.Entry(
            self,
            textvariable=self._game_user_dir_var,
            validate="focusout",
            validatecommand=self.on_game_user_dir_change,
        )
        self._game_user_dir_button = tkinter.ttk.Button(
            self,
            text="Find",
            command=self.on_game_user_dir_button,
        )
        self._game_user_dir_label.grid(row=row, column=0, sticky=tkinter.E)
        self._game_user_dir_entry.grid(row=row, column=1, sticky=tkinter.W+tkinter.E)
        self._game_user_dir_button.grid(row=row, column=2, sticky=tkinter.W+tkinter.E)
        row += 1

        # Go button
        self._go_button = tkinter.ttk.Button(
            self,
            text="Go!",
            command=self.on_go_button,
        )
        self._go_button.grid(row=row, column=1)

    def init_db(self) -> None:
        """Initialises the database handle."""
        self._db = DB()

    def on_go_button(self) -> None:
        """Handler for the go button."""
        game_key: str
        game_key = self._game_sel_var.get() # type: ignore
        game_root_dir: str
        game_root_dir = self._game_root_dir_var.get() # type: ignore
        game_user_dir: str
        game_user_dir = self._game_user_dir_var.get() # type: ignore

        if game_key not in REACTOR_CONSTRUCTORS:
            tkinter.messagebox.showerror(
                title="Error - Goodsplit",
                message=f"Please select a valid game.\nThe game key {game_key!r} is not valid or not supported.",
            )
        else:
            window = TkGameWindow(
                game_key=game_key,
                game_root_dir=game_root_dir,
                game_user_dir=game_user_dir,
            )
            self._active_windows.append(window)

    def on_game_select(self, ev: tkinter.Event) -> None:
        """Handler for selecting the game."""
        game_key: str
        game_key = self._game_sel_var.get() # type: ignore
        game_root_dir = self._db.get_game_root_dir(
            game_id=self._db.ensure_game_id(
                game_key=game_key,
                game_title=REACTORS[game_key].get_game_title(),
            ),
        )
        game_user_dir = self._db.get_game_user_dir(
            game_id=self._db.ensure_game_id(
                game_key=game_key,
                game_title=REACTORS[game_key].get_game_title(),
            ),
        )
        self._game_root_dir_var.set(game_root_dir) # type: ignore
        self._game_user_dir_var.set(game_user_dir) # type: ignore
        self._game_root_dir_entry.icursor(tkinter.END) # type: ignore
        self._game_user_dir_entry.icursor(tkinter.END) # type: ignore
        self._game_root_dir_entry.xview(tkinter.END) # type: ignore
        self._game_user_dir_entry.xview(tkinter.END) # type: ignore

    def find_existing_path_parent(self, path: Path) -> Path:
        """Finds the first path that exists given a path name."""

        while (not path.exists()) and path and (path.parent != path):
            path = path.parent

        return path

    def on_game_root_dir_button(self) -> None:
        """Handler for selecting the game root dir."""
        initialdir: str
        initialdir = self._game_root_dir_var.get() # type: ignore
        do_initialdir = False
        if initialdir:
            initialdir_path = self.find_existing_path_parent(Path(initialdir))
            if initialdir_path.parent != initialdir_path:
                do_initialdir = True
                initialdir = str(initialdir_path)

        result: str
        if do_initialdir:
            result = tkinter.filedialog.askdirectory(
                initialdir=initialdir,
            ) # type: ignore
        else:
            result = tkinter.filedialog.askdirectory() # type: ignore

        if result:
            self._game_root_dir_var.set(result) # type: ignore
            self.on_game_root_dir_change()

    def on_game_root_dir_change(self, *args: Any) -> None:
        """Handler called whenever the game root dir changes."""
        result: str
        result = self._game_root_dir_var.get() # type: ignore
        game_key: str
        game_key = self._game_sel_var.get() # type: ignore
        if game_key in REACTORS:
            self._db.set_game_root_dir(
                game_id=self._db.ensure_game_id(
                    game_key=game_key,
                    game_title=REACTORS[game_key].get_game_title(),
                ),
                game_root_dir=result,
            )

    def on_game_user_dir_button(self) -> None:
        """Handler for selecting the game user dir."""
        result: str
        result = tkinter.filedialog.askdirectory() # type: ignore
        if result:
            self._game_user_dir_var.set(result) # type: ignore
            self.on_game_user_dir_change()

    def on_game_user_dir_change(self, *args: Any) -> None:
        """Handler called whenever the game user dir changes."""
        result: str
        result = self._game_user_dir_var.get() # type: ignore
        game_key: str
        game_key = self._game_sel_var.get() # type: ignore
        if game_key in REACTORS:
            self._db.set_game_user_dir(
                game_id=self._db.ensure_game_id(
                    game_key=game_key,
                    game_title=REACTORS[game_key].get_game_title(),
                ),
                game_user_dir=result,
            )
