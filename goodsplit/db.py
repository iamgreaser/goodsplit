import datetime
import logging
from pathlib import Path

import sqlalchemy.engine.url

LOG = logging.getLogger("db")

class DB:
    """A Goodsplit SQLite 3 database handle."""
    __slots__ = (
        "_sql_engine",
    )

    def __init__(self) -> None:
        path = Path("~/goodsplit-times.sqlite3").expanduser().resolve()
        LOG.info(f"Opening {path}")
        self._sql_engine = sqlalchemy.create_engine(
            sqlalchemy.engine.url.URL(
                drivername="sqlite",
                database=str(path),
            )
        )
        self._prepare_sql_schema()

    def _prepare_sql_schema(self) -> None:
        # Set up our tables
        with self._sql_engine.connect() as C:
            #
            # Firstly, we have our game.
            #

            # Games (has key)
            LOG.info(f"Ensuring games table")
            C.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER NOT NULL PRIMARY KEY ASC ON CONFLICT ROLLBACK AUTOINCREMENT,
                    type_key TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL UNIQUE,
                    game_root_dir TEXT NOT NULL DEFAULT '',
                    game_user_dir TEXT NOT NULL DEFAULT ''
                );
            """)

            #
            # A game has time bases and fuse split types.
            #

            # Time bases (ref: Game) (has key)
            LOG.info(f"Ensuring time_bases table")
            C.execute("""
                CREATE TABLE IF NOT EXISTS time_bases (
                    id INTEGER NOT NULL PRIMARY KEY ASC ON CONFLICT ROLLBACK AUTOINCREMENT,
                    game_id INTEGER NOT NULL REFERENCES games(id),
                    type_key TEXT NOT NULL
                );
            """)
            C.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    time_bases_unique_game_id_type_key
                    ON time_bases(game_id, type_key);
            """)

            # Fuse split types (ref: Game) (has key)
            LOG.info(f"Ensuring fuse_split_types table")
            C.execute("""
                CREATE TABLE IF NOT EXISTS fuse_split_types (
                    id INTEGER NOT NULL PRIMARY KEY ASC ON CONFLICT ROLLBACK AUTOINCREMENT,
                    game_id INTEGER NOT NULL REFERENCES games(id),
                    type_key TEXT NOT NULL
                );
            """)
            C.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    fuse_split_types_unique_game_id_type_key
                    ON time_bases(game_id, type_key);
            """)

            #
            # A game also has runs.
            #

            # Runs (ref: Game)
            LOG.info(f"Ensuring runs table")
            C.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER NOT NULL PRIMARY KEY ASC ON CONFLICT ROLLBACK AUTOINCREMENT,
                    game_id INTEGER NOT NULL REFERENCES games(id),
                    run_start_datetime TEXT NOT NULL
                );
            """)
            C.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    runs_unique_game_id_run_start_datetime
                    ON runs(game_id, run_start_datetime);
            """)

            #
            # With a run and a few time bases, we need to assign times to splits.
            #

            # Fuse splits (ref: Run) (ref: Fuse split type)
            LOG.info(f"Ensuring splits table")
            C.execute("""
                CREATE TABLE IF NOT EXISTS splits (
                    id INTEGER NOT NULL PRIMARY KEY ASC ON CONFLICT ROLLBACK AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES runs(id),
                    fuse_split_type_id INTEGER NOT NULL REFERENCES fuse_split_types(id)
                );
            """)
            C.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    fuse_splits_unique_run_id_fuse_split_type_id
                    ON splits(run_id, fuse_split_type_id);
            """)

            # Time stamps (ref: Split) (ref: Time base)
            LOG.info(f"Ensuring time_stamps table")
            C.execute("""
                CREATE TABLE IF NOT EXISTS time_stamps (
                    id INTEGER NOT NULL PRIMARY KEY ASC ON CONFLICT ROLLBACK AUTOINCREMENT,
                    split_id INTEGER NOT NULL REFERENCES splits(id),
                    time_base_id INTEGER NOT NULL REFERENCES time_bases(id),
                    value_microseconds INT8 NOT NULL
                );
            """)
            C.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    time_stamps_unique_split_id_time_base_id
                    ON time_stamps(split_id, time_base_id);
            """)

    def fetch_timestamp_now(self) -> str:
        """Fetches a timestamp of now in ISO format with microseconds."""
        pre_subs, _, post_subs = datetime.datetime.utcnow().isoformat("T").partition(".")
        result = (pre_subs + "." + (post_subs + ("0"*6))[:6])
        return result

    def ensure_game_id(self, *, game_key: str, game_title: str) -> int:
        """Gets the database ID for the game, creating it if necessary."""
        # Get, and if empty then dump
        with self._sql_engine.connect() as C:
            rows = C.execute("""
                SELECT id FROM games WHERE type_key = ? LIMIT 1
            """, [
                game_key
            ])

            # Did we get an ID?
            row = rows.fetchone()
            if row:
                # Yes - return it
                return int(row[0])

            # Otherwise... no - add it
            LOG.info(f"Adding game ID {game_key!r} -> {game_title!r}")
            C.execute("""
                INSERT INTO games(type_key, title) VALUES (?, ?)
            """, [
                game_key,
                game_title,
            ])
            rows = C.execute("""
                SELECT id FROM games WHERE type_key = ? LIMIT 1
            """, [
                game_key
            ])

            # Did we get an ID?
            row = rows.fetchone()
            # Well, we got an ID, or something went horribly wrong
            result = int(row[0])
            return result

    def ensure_fuse_split_type(self, *, game_id: int, type_key: str) -> int:
        """Gets the database ID for the fuse split type, creating it if necessary."""
        # Get, and if empty then dump
        with self._sql_engine.connect() as C:
            rows = C.execute("""
                SELECT id FROM fuse_split_types WHERE game_id = ? AND type_key = ? LIMIT 1
            """, [
                game_id,
                type_key,
            ])

            # Did we get an ID?
            row = rows.fetchone()
            if row:
                # Yes - return it
                return int(row[0])

            # Otherwise... no - add it
            LOG.info(f"Adding fuse split type ID {game_id!r} {type_key!r}")
            C.execute("""
                INSERT INTO fuse_split_types(game_id, type_key) VALUES (?, ?)
            """, [
                game_id,
                type_key,
            ])
            rows = C.execute("""
                SELECT id FROM fuse_split_types WHERE game_id = ? AND type_key = ? LIMIT 1
            """, [
                game_id,
                type_key,
            ])

            # Did we get an ID?
            # Well, we got an ID, or something went horribly wrong
            row = rows.fetchone()
            result = int(row[0])
            return result

    def ensure_time_base_id(self, *, game_id: int, type_key: str) -> int:
        """Gets the database ID for the time base type, creating it if necessary."""
        # Get, and if empty then dump
        with self._sql_engine.connect() as C:
            rows = C.execute("""
                SELECT id FROM time_bases WHERE game_id = ? AND type_key = ? LIMIT 1
            """, [
                game_id,
                type_key,
            ])

            # Did we get an ID?
            row = rows.fetchone()
            if row:
                # Yes - return it
                return int(row[0])

            # Otherwise... no - add it
            LOG.info(f"Adding time base ID {game_id!r} {type_key!r}")
            C.execute("""
                INSERT INTO time_bases(game_id, type_key) VALUES (?, ?)
            """, [
                game_id,
                type_key,
            ])
            rows = C.execute("""
                SELECT id FROM time_bases WHERE game_id = ? AND type_key = ? LIMIT 1
            """, [
                game_id,
                type_key,
            ])

            # Did we get an ID?
            row = rows.fetchone()
            # Well, we got an ID, or something went horribly wrong
            result = int(row[0])
            return result

    def create_run_id(self, *, game_id: int) -> int:
        """Creates a run for now and returns its ID."""

        with self._sql_engine.connect() as C:
            run_start_datetime = self.fetch_timestamp_now()
            LOG.info(f"Adding run game={game_id!r} start={run_start_datetime!r}")
            C.execute("""
                INSERT INTO runs(game_id, run_start_datetime) VALUES (?, ?)
            """, [
                game_id,
                run_start_datetime,
            ])
            rows = C.execute("""
                SELECT id FROM runs WHERE game_id = ? AND run_start_datetime = ? LIMIT 1
            """, [
                game_id,
                run_start_datetime,
            ])

            # Did we get an ID?
            row = rows.fetchone()
            # Well, we got an ID, or something went horribly wrong
            result = int(row[0])
            return result

    def create_split_id(self, *, run_id: int, fuse_split_type_id: int) -> int:
        """Creates a split and returns its ID."""

        with self._sql_engine.connect() as C:
            LOG.info(f"Adding split run={run_id!r} fuse_split_type={fuse_split_type_id!r}")
            C.execute("""
                INSERT INTO splits(run_id, fuse_split_type_id) VALUES (?, ?)
            """, [
                run_id,
                fuse_split_type_id,
            ])
            rows = C.execute("""
                SELECT id FROM splits WHERE run_id = ? AND fuse_split_type_id = ? LIMIT 1
            """, [
                run_id,
                fuse_split_type_id,
            ])

            # Did we get an ID?
            row = rows.fetchone()
            # Well, we got an ID, or something went horribly wrong
            result = int(row[0])
            return result

    def create_time_stamp_id(self, *, split_id: int, time_base_id: int, value_microseconds: int) -> int:
        """Creates a time stamp and returns its ID."""

        with self._sql_engine.connect() as C:
            LOG.info(f"Adding time stamp split={split_id!r} time_base={time_base_id!r} value={value_microseconds!r}")
            C.execute("""
                INSERT INTO time_stamps(split_id, time_base_id, value_microseconds) VALUES (?, ?, ?)
            """, [
                split_id,
                time_base_id,
                value_microseconds,
            ])
            rows = C.execute("""
                SELECT id FROM time_stamps WHERE split_id = ? AND time_base_id = ? LIMIT 1
            """, [
                split_id,
                time_base_id,
            ])

            # Did we get an ID?
            row = rows.fetchone()
            # Well, we got an ID, or something went horribly wrong
            result = int(row[0])
            return result

    def get_game_root_dir(self, *, game_id: int) -> str:
        """Gets the root dir for the game."""
        with self._sql_engine.connect() as C:
            rows = C.execute("""
                SELECT game_root_dir FROM games WHERE id = ? LIMIT 1
            """, [
                game_id
            ])

            # Did we get a row?
            row = rows.fetchone()
            # Well, we got a row, or something went horribly wrong
            result = row[0]
            assert isinstance(result, str)
            return result

    def get_game_user_dir(self, *, game_id: int) -> str:
        """Gets the user dir for the game."""
        with self._sql_engine.connect() as C:
            rows = C.execute("""
                SELECT game_user_dir FROM games WHERE id = ? LIMIT 1
            """, [
                game_id
            ])

            # Did we get a row?
            row = rows.fetchone()
            # Well, we got a row, or something went horribly wrong
            result = row[0]
            assert isinstance(result, str)
            return result

    def set_game_root_dir(self, *, game_id: int, game_root_dir: str) -> None:
        """Sets the root dir for the game."""
        with self._sql_engine.connect() as C:
            C.execute("""
                UPDATE games SET game_root_dir = ? WHERE id = ?
            """, [
                game_root_dir,
                game_id
            ])

    def set_game_user_dir(self, *, game_id: int, game_user_dir: str) -> None:
        """Sets the user dir for the game."""
        with self._sql_engine.connect() as C:
            C.execute("""
                UPDATE games SET game_user_dir = ? WHERE id = ?
            """, [
                game_user_dir,
                game_id
            ])
