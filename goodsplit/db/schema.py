import datetime
import logging
from pathlib import Path

import sqlalchemy
import sqlalchemy as SQL

LOG = logging.getLogger("db_schema")

metadata = SQL.MetaData()


#
# Firstly, we have our game.
#

# Games (has key)
games = SQL.Table("games", metadata,
    SQL.Column("id", SQL.Integer, nullable=False, primary_key=True, autoincrement=True),
    SQL.Column("type_key", SQL.String, nullable=False, unique=True),
    SQL.Column("title", SQL.String, nullable=False, unique=True),
    SQL.Column("game_root_dir", SQL.String, nullable=False, server_default=""),
    SQL.Column("game_user_dir", SQL.String, nullable=False, server_default=""),
)


#
# A game has time bases and fuse split types.
#

# Time bases (ref: Game) (has key)
time_bases = SQL.Table("time_bases", metadata,
    SQL.Column("id", SQL.Integer, nullable=False, primary_key=True, autoincrement=True),
    SQL.Column("game_id", SQL.ForeignKey("games.id"), nullable=False),
    SQL.Column("type_key", SQL.String, nullable=False),
    SQL.Index("time_bases_unique_game_id_type_key", "game_id", "type_key", unique=True),
)

# Fuse split types (ref: Game) (has key)
fuse_split_types = SQL.Table("fuse_split_types", metadata,
    SQL.Column("id", SQL.Integer, nullable=False, primary_key=True, autoincrement=True),
    SQL.Column("game_id", SQL.ForeignKey("games.id"), nullable=False),
    SQL.Column("type_key", SQL.String, nullable=False),
    SQL.Index("fuse_split_types_unique_game_id_type_key", "game_id", "type_key", unique=True),
)


#
# A game also has runs.
#

# Runs (ref: Game)
runs = SQL.Table("runs", metadata,
    SQL.Column("id", SQL.Integer, nullable=False, primary_key=True, autoincrement=True),
    SQL.Column("game_id", SQL.ForeignKey("games.id"), nullable=False),
    SQL.Column("run_start_datetime", SQL.String, nullable=False),
    SQL.Index("runs_unique_game_id_run_start_datetime", "game_id", "run_start_datetime", unique=True),
)


#
# With a run and a few time bases, we need to assign times to splits.
#

# Fuse splits (ref: Run) (ref: Fuse split type)
splits = SQL.Table("splits", metadata,
    SQL.Column("id", SQL.Integer, nullable=False, primary_key=True, autoincrement=True),
    SQL.Column("run_id", SQL.ForeignKey("runs.id"), nullable=False),
    SQL.Column("fuse_split_type_id", SQL.ForeignKey("fuse_split_types.id"), nullable=False),
    SQL.Index("splits_unique_run_id_fuse_spit_type_id", "run_id", "fuse_split_type_id", unique=True),
)

# Time stamps (ref: Split) (ref: Time base)
LOG.info(f"Ensuring time_stamps table")
time_stamps = SQL.Table("time_stamps", metadata,
    SQL.Column("id", SQL.Integer, nullable=False, primary_key=True, autoincrement=True),
    SQL.Column("split_id", SQL.ForeignKey("splits.id"), nullable=False),
    SQL.Column("time_base_id", SQL.ForeignKey("time_bases.id"), nullable=False),
    SQL.Column("value_microseconds", SQL.BigInteger, nullable=False),
    SQL.Index("time_stamps_unique_split_id_time_base_id", "split_id", "time_base_id", unique=True),
)
