import datetime
import logging
from pathlib import Path

import sqlalchemy
import sqlalchemy as SQL
import sqlalchemy.engine.url

LOG = logging.getLogger("db")

from . import schema
from . import schema as S

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
        """Creates all of the tables in our database if they don't exist already."""
        schema.metadata.create_all(self._sql_engine)

    def fetch_timestamp_now(self) -> str:
        """Fetches a timestamp of now in ISO format with microseconds."""
        pre_subs, _, post_subs = datetime.datetime.utcnow().isoformat("T").partition(".")
        result = (pre_subs + "." + (post_subs + ("0"*6))[:6])
        return result

    def ensure_game_id(self, *, game_key: str, game_title: str) -> int:
        """Gets the database ID for the game, creating it if necessary."""
        # Get, and if empty then dump
        with self._sql_engine.connect() as C:
            rows = (C.execute(SQL.select([S.games.c.id]).limit(1)
                .where(S.games.c.type_key == game_key)))

            # Did we get an ID?
            row = rows.fetchone()
            if row:
                # Yes - return it
                return int(row[0])

            # Otherwise... no - add it
            LOG.info(f"Adding game ID {game_key!r} -> {game_title!r}")
            C.execute(S.games.insert()
                .values(type_key=game_key, title=game_title))

            # Did we get an ID?
            # Well, we got an ID, or something went horribly wrong
            rows = (C.execute(SQL.select([S.games.c.id]).limit(1)
                .where(S.games.c.type_key == game_key)))
            row = rows.fetchone()
            result = int(row[0])
            return result

    def ensure_fuse_split_type(self, *, game_id: int, type_key: str) -> int:
        """Gets the database ID for the fuse split type, creating it if necessary."""
        # Get, and if empty then dump
        with self._sql_engine.connect() as C:
            rows = (C.execute(SQL.select([S.fuse_split_types.c.id]).limit(1)
                .where(S.fuse_split_types.c.game_id == game_id)
                .where(S.fuse_split_types.c.type_key == type_key)))

            # Did we get an ID?
            row = rows.fetchone()
            if row:
                # Yes - return it
                return int(row[0])

            # Otherwise... no - add it
            LOG.info(f"Adding fuse split type ID {game_id!r} {type_key!r}")
            C.execute(S.fuse_split_types.insert()
                .values(game_id=game_id, type_key=type_key))

            # Did we get an ID?
            # Well, we got an ID, or something went horribly wrong
            rows = (C.execute(SQL.select([S.fuse_split_types.c.id]).limit(1)
                .where(S.fuse_split_types.c.game_id == game_id)
                .where(S.fuse_split_types.c.type_key == type_key)))
            row = rows.fetchone()
            result = int(row[0])
            return result

    def ensure_time_base_id(self, *, game_id: int, type_key: str) -> int:
        """Gets the database ID for the time base type, creating it if necessary."""
        # Get, and if empty then dump
        with self._sql_engine.connect() as C:
            rows = (C.execute(SQL.select([S.time_bases.c.id]).limit(1)
                .where(S.time_bases.c.game_id == game_id)
                .where(S.time_bases.c.type_key == type_key)))

            # Did we get an ID?
            row = rows.fetchone()
            if row:
                # Yes - return it
                return int(row[0])

            # Otherwise... no - add it
            LOG.info(f"Adding time base ID {game_id!r} {type_key!r}")
            C.execute(S.time_bases.insert()
                .values(game_id=game_id, type_key=type_key))

            # Did we get an ID?
            # Well, we got an ID, or something went horribly wrong
            rows = (C.execute(SQL.select([S.time_bases.c.id]).limit(1)
                .where(S.time_bases.c.game_id == game_id)
                .where(S.time_bases.c.type_key == type_key)))
            row = rows.fetchone()
            result = int(row[0])
            return result

    def create_run_id(self, *, game_id: int) -> int:
        """Creates a run for now and returns its ID."""

        with self._sql_engine.connect() as C:
            run_start_datetime = self.fetch_timestamp_now()
            LOG.info(f"Adding run game={game_id!r} start={run_start_datetime!r}")
            C.execute(S.runs.insert()
                .values(game_id=game_id, run_start_datetime=run_start_datetime))

            # Did we get an ID?
            # Well, we got an ID, or something went horribly wrong
            rows = (C.execute(SQL.select([S.runs.c.id]).limit(1)
                .where(S.runs.c.game_id == game_id)
                .where(S.runs.c.run_start_datetime == run_start_datetime)))
            row = rows.fetchone()
            result = int(row[0])
            return result

    def create_split_id(self, *, run_id: int, fuse_split_type_id: int) -> int:
        """Creates a split and returns its ID."""

        with self._sql_engine.connect() as C:
            LOG.info(f"Adding split run={run_id!r} fuse_split_type={fuse_split_type_id!r}")
            C.execute(S.splits.insert()
                .values(run_id=run_id, fuse_split_type_id=fuse_split_type_id))

            # Did we get an ID?
            # Well, we got an ID, or something went horribly wrong
            rows = (C.execute(SQL.select([S.splits.c.id]).limit(1)
                .where(S.splits.c.run_id == run_id)
                .where(S.splits.c.fuse_split_type_id == fuse_split_type_id)))
            row = rows.fetchone()
            result = int(row[0])
            return result

    def create_time_stamp_id(self, *, split_id: int, time_base_id: int, value_microseconds: int) -> int:
        """Creates a time stamp and returns its ID."""

        with self._sql_engine.connect() as C:
            LOG.info(f"Adding time stamp split={split_id!r} time_base={time_base_id!r} value={value_microseconds!r}")
            C.execute(S.time_stamps.insert().values(
                split_id=split_id,
                time_base_id=time_base_id,
                value_microseconds=value_microseconds,
            ))
            # Did we get an ID?
            # Well, we got an ID, or something went horribly wrong
            rows = C.execute(SQL.select([S.time_stamps.c.id]).limit(1),
                split_id=split_id,
                time_base_id=time_base_id,
            )
            row = rows.fetchone()
            result = int(row[0])
            return result

    def get_game_root_dir(self, *, game_id: int) -> str:
        """Gets the root dir for the game."""
        with self._sql_engine.connect() as C:
            # Did we get a row?
            # Well, we got a row, or something went horribly wrong
            rows = C.execute(SQL.select([S.games.c.game_root_dir]).limit(1),
                id=game_id,
            )
            row = rows.fetchone()
            result = row[0]
            assert isinstance(result, str)
            return result

    def get_game_user_dir(self, *, game_id: int) -> str:
        """Gets the user dir for the game."""
        with self._sql_engine.connect() as C:
            # Did we get a row?
            # Well, we got a row, or something went horribly wrong
            rows = C.execute(SQL.select([S.games.c.game_user_dir]).limit(1),
                id=game_id,
            )
            row = rows.fetchone()
            result = row[0]
            assert isinstance(result, str)
            return result

    def set_game_root_dir(self, *, game_id: int, game_root_dir: str) -> None:
        """Sets the root dir for the game."""
        with self._sql_engine.connect() as C:
            C.execute(S.games.update()
                .where(S.games.c.id == game_id)
                .values(game_root_dir=game_root_dir))

    def set_game_user_dir(self, *, game_id: int, game_user_dir: str) -> None:
        """Sets the user dir for the game."""
        with self._sql_engine.connect() as C:
            C.execute(S.games.update()
                .where(S.games.c.id == game_id)
                .values(game_user_dir=game_user_dir))
