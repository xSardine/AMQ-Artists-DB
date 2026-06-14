import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from functools import lru_cache
from typing import Any, Iterator, Pattern

from song_filters import SongFilters

DATABASE_PATH = Path("data") / "Enhanced-AMQ-Database.db"

SongFullRow = tuple[Any, ...]
SqlRows = list[SongFullRow]


class DatabaseQueryError(Exception):
    """SQLite query or connection failed."""


@lru_cache(maxsize=None)
def extract_song_database() -> dict[int, SongFullRow]:
    """Extract the song database"""

    command = "SELECT * FROM songsFull"
    song_database = {}

    with database_cursor() as cursor:
        for song in run_sql_command(cursor, command):
            song_database[song[13]] = song

    return song_database


@lru_cache(maxsize=None)
def extract_anime_database() -> dict[int, dict[str, Any]]:
    """Extract the anime database"""

    command = "SELECT * FROM songsFull"
    anime_database = {}

    with database_cursor() as cursor:
        for song in run_sql_command(cursor, command):
            if song[0] not in anime_database:
                anime_database[song[0]] = {
                    "animeJPName": song[6],
                    "animeENName": song[7],
                    "animeAltNames": song[9],
                    "animeVintage": song[10],
                    "animeType": song[11],
                    "animeCategory": song[12],
                    "songs": [],
                }
            anime_database[song[0]]["songs"].append(song)

    return anime_database


@lru_cache(maxsize=None)
def extract_artist_database() -> dict[str, dict[str, Any]]:
    """Extract the artist database"""

    with database_cursor() as cursor:
        basic_info = run_sql_command(
            cursor,
            "SELECT id, romaji_names, disambiguation, type FROM artistsNames"
        )
        artist_groups = run_sql_command(
            cursor,
            "SELECT id, groups, groups_line_up FROM artistsGroups"
        )
        line_ups_members = run_sql_command(
            cursor,
            "SELECT artist_id, line_up_id, line_up_type, members, members_line_up FROM lineUpsMembers",
        )

        if len(basic_info) != len(artist_groups):
            print("ERROR EXTRACTING ARTIST DATABASE")
            return {}

        artist_database = {}
        for info, groups in zip(basic_info, artist_groups):
            if info[0] != groups[0]:
                print("ERROR EXTRACTING ARTIST DATABASE")
                return {}

            artist_database[str(info[0])] = {
                "names": info[1].split("\\$"),
                "groups": (
                    [
                        [group, int(line_up)]
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

            artist = artist_database[str(line_up_members[0])]

            # retrieve info from the artist
            for info in basic_info:
                if info[0] == line_up_members[0]:
                    break

            if info[0] != line_up_members[0]:
                print(f"ERROR EXTRACTING ARTIST DATABASE on {line_up_members[0]}")
                return {}

            if line_up_members[1] != len(artist["line_ups"]):
                print(f"ERROR EXTRACTING ARTIST DATABASE on {line_up_members[0]}")
                return {}

            current_lu = []
            for member_id, member_line_up_id in zip(
                line_up_members[3].split(","), line_up_members[4].split(",")
            ):
                current_lu.append([member_id, int(member_line_up_id)])

            artist["line_ups"].append(
                {
                    "line_up_type": line_up_members[2],
                    "members": current_lu,
                }
            )

    return artist_database


def run_sql_command(cursor, sql_command, data=None) -> SqlRows:
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


@lru_cache(maxsize=128)
def _compiled_regexp(pattern: str) -> Pattern[str] | None:
    """Compile a REGEXP pattern once; reused across all row comparisons in one query."""
    try:
        return re.compile(pattern)
    except re.error:
        return None


def regexp(expr: str, item: str | None) -> bool:
    """SQLite REGEXP callback: return whether expr matches item (used by connect_to_database)."""
    if not item:
        return False
    reg = _compiled_regexp(expr)
    if reg is None:
        return False
    return reg.search(item) is not None


def connect_to_database(path: Path | str = DATABASE_PATH) -> sqlite3.Cursor:
    """Connect to the database and return the connection's cursor"""
    try:
        sqlite_connection = sqlite3.connect(path)
        sqlite_connection.create_function("REGEXP", 2, regexp)
        cursor = sqlite_connection.cursor()
        return cursor
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


def get_random_songs(limit: int, filters: SongFilters | None = None) -> list[SongFullRow]:
    """
    Return up to `limit` random rows from songsFull.
    When `filters` is None, no WHERE clause is applied (legacy /api/get_50_random_songs).
    """
    with database_cursor() as cursor:
        if filters is None:
            query = "SELECT * FROM songsFull ORDER BY RANDOM() LIMIT ?"
            return run_sql_command(cursor, query, [limit])

        where, params = filters.songs_full_where()
        query = f"SELECT * FROM songsFull WHERE {where} ORDER BY RANDOM() LIMIT ?"
        params.append(limit)
        return run_sql_command(cursor, query, params)


def _get_songs_list_by_column_in(column: str, ids, filters: SongFilters) -> SqlRows:
    """Fetch songsFull rows where `column` is in `ids`, applying SongFilters in SQL."""
    placeholders = ",".join("?" * len(ids))
    where, params = filters.songs_full_where(
        middle_sql=f" AND {column} IN ({placeholders})",
        middle_params=ids,
    )
    query = f"SELECT * FROM songsFull WHERE {where}"
    with database_cursor() as cursor:
        return run_sql_command(cursor, query, params)


def get_songs_list_from_ann_ids(ann_ids, filters: SongFilters) -> SqlRows:
    return _get_songs_list_by_column_in("annId", ann_ids, filters)


def get_songs_list_from_mal_ids(mal_ids, filters: SongFilters) -> SqlRows:
    return _get_songs_list_by_column_in("malId", mal_ids, filters)


def get_songs_list_from_ann_song_ids(ann_song_ids, filters: SongFilters) -> SqlRows:
    return _get_songs_list_by_column_in("annSongId", ann_song_ids, filters)


def get_songs_list_from_amq_song_ids(amq_song_ids, filters: SongFilters) -> SqlRows:
    return _get_songs_list_by_column_in("amqSongId", amq_song_ids, filters)


def get_song_list_from_songArtist(regex, filters: SongFilters, match_case: bool = False) -> SqlRows:
    """Fallback artist search on romajiSongArtist when name-to-ID lookup finds nothing."""
    # TODO Indexes on lower ?
    song_artist_column = "romajiSongArtist" if match_case else "lower(romajiSongArtist)"
    where, params = filters.songs_full_where()
    query = (
        f"SELECT * FROM songsFull WHERE {where} "
        f"AND {song_artist_column} REGEXP ? LIMIT 500"
    )
    params.append(regex)
    with database_cursor() as cursor:
        return run_sql_command(cursor, query, params)


def get_song_ids_from_artist_ids(artist_ids) -> list[int]:
    """Return internal songs.id values for rows linked to any of the given artist IDs."""
    if not artist_ids:
        return []

    query = (
        f"SELECT song_id FROM link_song_artist WHERE artist_id IN ({','.join('?'*len(artist_ids))})"
    )
    params = [str(id) for id in artist_ids]
    with database_cursor() as cursor:
        rows = run_sql_command(cursor, query, params)
    return [int(row[0]) for row in rows]


def get_song_ids_from_composing_team_ids(composer_ids, arrangement: bool) -> list[int]:
    """
    Return internal songs.id values credited to the given composer IDs.
    When arrangement is True, also includes songs where those IDs appear as arrangers.
    """
    if not composer_ids:
        return []

    placeholders = ",".join("?" * len(composer_ids))

    if arrangement:
        query = f"""
            SELECT song_id
            FROM link_song_composer
            WHERE composer_id IN ({placeholders})
            UNION
            SELECT song_id
            FROM link_song_arranger
            WHERE arranger_id IN ({placeholders})
            LIMIT 500
        """
        params = composer_ids + composer_ids
    else:
        query = f"""
            SELECT song_id
            FROM link_song_composer
            WHERE composer_id IN ({placeholders})
            LIMIT 500
        """
        params = composer_ids

    with database_cursor() as cursor:
        rows = run_sql_command(cursor, query, params)
    return [int(row[0]) for row in rows]


def get_artist_ids_from_regex(regex, match_case: bool = False) -> list[int]:
    """Match artist names with REGEXP and return up to 50 distinct artist IDs."""
    # TODO Index on lower ?
    name_column = "romaji_name" if match_case else "lower(romaji_name)"
    query = (
        "SELECT artist_id FROM link_artist_name "
        f"WHERE {name_column} REGEXP ? GROUP BY artist_id LIMIT 50"
    )
    params = [regex]
    with database_cursor() as cursor:
        rows = run_sql_command(cursor, query, params)
    return [int(row[0]) for row in rows]


def get_songs_list_from_season(season, filters: SongFilters) -> SqlRows:
    """Get songs from a specific season, applying the shared SongFilters SQL rules."""
    where, params = filters.songs_full_where(
        middle_sql=" AND animeVintage LIKE ?",
        middle_params=[f"%{season}%"],
    )
    query = f"SELECT * FROM songsFull WHERE {where}"
    with database_cursor() as cursor:
        return run_sql_command(cursor, query, params)


def autocomplete_artists(search: str | None = None, count: int = 99999) -> list[str]:
    """Distinct romajiSongArtist values from songs, optionally filtered by substring."""
    with database_cursor() as cursor:
        query = "SELECT DISTINCT romajiSongArtist FROM songs"
        params = None
        if search:
            query += " WHERE romajiSongArtist LIKE ?"
            params = [f"%{search}%"]
        rows = run_sql_command(cursor, query, params)
    names = [row[0] for row in rows]
    return sorted(names, key=str.lower)[:count]


def autocomplete_song_names(search: str | None = None, count: int = 99999) -> list[str]:
    """Return sorted unique song names, optionally filtered by substring."""
    with database_cursor() as cursor:
        query = "SELECT DISTINCT romajiSongName FROM songs"
        params = None
        if search:
            query += " WHERE romajiSongName LIKE ?"
            params = [f"%{search}%"]
        rows = run_sql_command(cursor, query, params)
    return sorted((row[0] for row in rows), key=len)[:count]


def autocomplete_anime_names(song_name: str | None = None, song_artist: str | None = None) -> list[str]:
    """Distinct anime JP/EN titles from songsAnimes, optionally narrowed by song/artist."""
    with database_cursor() as cursor:
        query = "SELECT DISTINCT animeJPName, animeENName FROM songsAnimes"
        params = []
        conditions = []

        if song_name:
            conditions.append("romajiSongName = ?")
            params.append(song_name)
        if song_artist:
            conditions.append("romajiSongArtist = ?")
            params.append(song_artist)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        rows = run_sql_command(cursor, query, params)
    names = [row[0] or row[1] for row in rows]
    return sorted(names, key=str.lower)


def get_annid_linked_ids() -> dict[int, dict[str, Any]]:
    """Build annId -> linked external IDs and anime names from animesFull."""
    with database_cursor() as cursor:
        query = """
        SELECT
            annId, malId, anidbId, anilistId, kitsuId,
            animeENName, animeJPName, romaji_alt_names
        FROM animesFull
        """
        rows = run_sql_command(cursor, query)

    output: dict[int, dict[str, Any]] = {}
    for row in rows:
        (
            ann_id,
            mal_id,
            anidb_id,
            anilist_id,
            kitsu_id,
            anime_en_name,
            anime_jp_name,
            romaji_alt_names,
        ) = row
        alt_names_list = romaji_alt_names.split("\\$") if romaji_alt_names else []
        output[ann_id] = {
            "animeENName": anime_en_name,
            "animeJPName": anime_jp_name,
            "animeAltName": alt_names_list,
            "linked_ids": {
                "annId": ann_id,
                "myanimelist": mal_id,
                "anidb": anidb_id,
                "anilist": anilist_id,
                "kitsu": kitsu_id,
            },
        }
    return output


def get_database_totals() -> dict[str, Any]:
    """Aggregate song/anime/artist counts and breakdowns for /api/database_totals."""
    with database_cursor() as cursor:
        # Pass 1: one scan of `songs` for totals and song-level breakdowns.
        # total_anime = distinct annId (anime with at least one song in the catalog).
        stats_query = """
        SELECT
            COUNT(*) AS total_songs,
            COUNT(DISTINCT annId) AS total_anime,
            SUM(songType = 1) AS opening_count,
            SUM(songType = 2) AS ending_count,
            SUM(songType = 3) AS insert_count,
            SUM(isDub = 1) AS dub_count,
            SUM(isRebroadcast = 1) AS rebroadcast_count,
            SUM(isDub = 0 AND isRebroadcast = 0) AS normal_count,
            SUM(HQ IS NOT NULL) AS hq_count,
            SUM(MQ IS NOT NULL) AS mq_count,
            SUM(audio IS NOT NULL) AS audio_count
        FROM songs
        """
        results = run_sql_command(cursor, stats_query)
        first_row = results[0]

        # Pass 2: category names are open-ended; NULL categories are omitted.
        category_query = """
        SELECT songCategory, COUNT(*) AS count
        FROM songs
        WHERE songCategory IS NOT NULL
        GROUP BY songCategory
        """
        category_results = run_sql_command(cursor, category_query)

        # Pass 3: song rows per anime type (via songs JOIN animes), not distinct anime per type.
        anime_type_query = """
        SELECT COALESCE(a.animeType, 'No Type') AS anime_type, COUNT(*) AS count
        FROM songs s
        INNER JOIN animes a ON s.annId = a.annId
        GROUP BY COALESCE(a.animeType, 'No Type')
        """
        anime_type_results = run_sql_command(cursor, anime_type_query)

        # Pass 4: distinct season strings (animeVintage) among catalog songs.
        season_query = """
        SELECT COUNT(DISTINCT a.animeVintage) AS total_seasons
        FROM songs s
        INNER JOIN animes a ON s.annId = a.annId
        WHERE a.animeVintage IS NOT NULL
        """
        season_results = run_sql_command(cursor, season_query)

        # Pass 5: artists live in a separate table from songs.
        artist_results = run_sql_command(cursor, "SELECT COUNT(*) FROM artists")

    # HQ / MQ / audio buckets are not mutually exclusive (a song may have several links).
    return {
        "total_songs": first_row[0],
        "total_anime": first_row[1],
        "total_artists": artist_results[0][0],
        "total_seasons": season_results[0][0],
        "links_by_type": {
            "HQ": first_row[8],
            "MQ": first_row[9],
            "audio": first_row[10],
        },
        "songs_by_type": {
            "Opening": first_row[2],
            "Ending": first_row[3],
            "Insert": first_row[4],
        },
        "songs_by_broadcast": {
            "Dub": first_row[5],
            "Rebroadcast": first_row[6],
            "Normal": first_row[7],
        },
        "songs_by_category": {row[0]: row[1] for row in category_results},
        "songs_by_anime_type": {row[0]: row[1] for row in anime_type_results},
    }
