"""SQLite loading primitives used to construct the startup catalog."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from db_types import *

DATABASE_PATH = Path(__file__).resolve().parent / "data" / "Enhanced-AMQ-Database.db"


def load_song_rows() -> tuple[SongFullRow, ...]:
    """Load every songsFull row once at startup."""
    with database_cursor() as cursor:
        return tuple(run_sql_command(cursor, "SELECT * FROM songsFull"))


def load_artist_database() -> ArtistDatabase:
    """Load artist names, groups, and lineups during application startup."""
    with database_cursor() as cursor:
        basic_info = run_sql_command(
            cursor,
            "SELECT id, romaji_names, disambiguation, type FROM artistsNames",
        )
        artist_groups = run_sql_command(
            cursor,
            "SELECT id, groups, groups_line_up FROM artistsGroups",
        )
        line_ups_members = run_sql_command(
            cursor,
            "SELECT artist_id, line_up_id, line_up_type, members, members_line_up FROM lineUpsMembers",
        )

        if len(basic_info) != len(artist_groups):
            raise DatabaseQueryError(
                "Artist database extract failed: artistsNames/artistsGroups row count mismatch"
            )

        artist_database: ArtistDatabase = {}
        for info, groups in zip(basic_info, artist_groups):
            if info[0] != groups[0]:
                raise DatabaseQueryError(
                    "Artist database extract failed: artistsNames/artistsGroups "
                    f"id mismatch ({info[0]} vs {groups[0]})"
                )

            artist_database[str(info[0])] = {
                "names": info[1].split("\\$"),
                "groups": (
                    [
                        (int(group), int(line_up))
                        for group, line_up in zip(groups[1].split(","), groups[2].split(","))
                    ]
                    if groups[1]
                    else []
                ),
                "line_ups": [],
                "disambiguation": info[2],
                "type": info[3],
            }

        for line_up_members in line_ups_members:
            artist_id = str(line_up_members[0])
            artist = artist_database.get(artist_id)
            if artist is None:
                raise DatabaseQueryError(
                    f"Artist database extract failed: lineUpsMembers references "
                    f"unknown artist {artist_id}"
                )
            if line_up_members[1] != len(artist["line_ups"]):
                raise DatabaseQueryError(
                    f"Artist database extract failed: line-up index gap for "
                    f"artist {artist_id}"
                )

            artist["line_ups"].append(
                {
                    "line_up_type": line_up_members[2],
                    "members": tuple(
                        (int(member_id), int(member_line_up_id))
                        for member_id, member_line_up_id in zip(
                            line_up_members[3].split(","),
                            line_up_members[4].split(","),
                        )
                    ),
                }
            )

    return artist_database


def run_sql_command(cursor, sql_command, data=None) -> list[tuple[Any, ...]]:
    """Run a read SQL command; raise DatabaseQueryError on failure."""
    try:
        if data is not None:
            cursor.execute(sql_command, data)
        else:
            cursor.execute(sql_command)
        return cursor.fetchall()
    except sqlite3.Error as error:
        if data is not None:
            for param in data:
                if isinstance(param, str):
                    sql_command = sql_command.replace("?", '"' + str(param) + '"', 1)
                else:
                    sql_command = sql_command.replace("?", str(param), 1)
        print(f"\nError running SQL command:\n{sql_command}\n{error}\nData: {data}\n")
        raise DatabaseQueryError("Database query failed") from error


def connect_to_database(path: Path | str = DATABASE_PATH) -> sqlite3.Cursor:
    """Connect to the database and return the connection cursor."""
    try:
        connection = sqlite3.connect(path)
        return connection.cursor()
    except sqlite3.Error as error:
        raise DatabaseQueryError("Could not connect to database") from error


@contextmanager
def database_cursor(path: Path | str = DATABASE_PATH) -> Iterator[sqlite3.Cursor]:
    """Yield a database cursor and close its connection afterwards."""
    cursor = connect_to_database(path)
    try:
        yield cursor
    finally:
        cursor.connection.close()
