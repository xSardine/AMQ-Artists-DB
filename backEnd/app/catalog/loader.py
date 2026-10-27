"""Read one SQLite snapshot, decode records, and validate stored catalog data."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from catalog.indexes import build_catalog
from catalog.models import ArtistEntry, ArtistLineUp, Catalog, CatalogLoadError, Credits, Song

DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "Enhanced-AMQ-Database.db"


def load_catalog(path: Path | str = DATABASE_PATH, transform=None) -> Catalog:
    """Read all source tables in one transaction, then build the in-memory catalog."""
    with _database_connection(path) as connection:
        database_updated_at = _load_updated_at(connection)
        songs = _load_songs(connection)
        artists = _load_artists(connection)
        genres = tuple(
            (row["annId"], row["genre"])
            for row in _read_rows(connection, "SELECT annId, genre FROM link_anime_genre")
        )
        tags = tuple(
            (row["annId"], row["tag"])
            for row in _read_rows(connection, "SELECT annId, tag FROM link_anime_tag")
        )
    if transform is not None:
        songs, artists = transform(songs, artists)
    return build_catalog(songs, artists, genres, tags, database_updated_at=database_updated_at)


def _load_updated_at(connection: sqlite3.Connection) -> str | None:
    """Read the conversion timestamp; older databases have no metadata table."""
    if not connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'database_metadata'"
    ).fetchone():
        return None
    row = connection.execute(
        "SELECT value FROM database_metadata WHERE key = 'updated_at'"
    ).fetchone()
    return row["value"] if row else None


@contextmanager
def _database_connection(path: Path | str) -> Iterator[sqlite3.Connection]:
    """Open a read-only transaction and close it on success or failure."""
    try:
        connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    except sqlite3.Error as error:
        raise CatalogLoadError("Could not connect to database") from error
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")
        yield connection
    except sqlite3.Error as error:
        raise CatalogLoadError("Could not read database snapshot") from error
    finally:
        connection.close()


def _read_rows(connection: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    try:
        with closing(connection.execute(sql)) as cursor:
            return cursor.fetchall()
    except sqlite3.Error as error:
        raise CatalogLoadError(f"Database query failed: {sql}") from error


def _load_songs(connection: sqlite3.Connection) -> tuple[Song, ...]:
    rows = _read_rows(
        connection,
        """
            SELECT
                annId, malId, anidbId, anilistId, kitsuId,
                originalJPName, animeJPName, animeENName, original_alt_names, romaji_alt_names,
                animeVintage, animeType, animeCategory, songId, annSongId,
                amqSongId, songType, songNumber, songCategory, originalSongName,
                romajiSongName, originalSongArtist, romajiSongArtist, artists, artists_line_up,
                originalSongComposer, romajiSongComposer, composers, composers_line_up,
                originalSongArranger,
                romajiSongArranger, arrangers, arrangers_line_up, songDifficulty, isDub,
                isRebroadcast, songLength, HQ, MQ, audio
            FROM songsFull
        """,
    )
    return tuple(_decode_song(row) for row in rows)


def _load_artists(connection: sqlite3.Connection) -> dict[int, ArtistEntry]:
    basic_info = _read_rows(
        connection,
        "SELECT id, romaji_names, original_names, disambiguation, type FROM artistsNames",
    )
    group_rows = _read_rows(connection, "SELECT id, groups, groups_line_up FROM artistsGroups")
    lineup_rows = _read_rows(
        connection,
        "SELECT artist_id, line_up_id, line_up_type, members, members_line_up "
        "FROM lineUpsMembers ORDER BY artist_id, line_up_id",
    )
    if len(basic_info) != len(group_rows):
        raise CatalogLoadError(
            "Artist database extract failed: artistsNames/artistsGroups row count mismatch"
        )

    groups_by_artist = {row["id"]: row for row in group_rows}
    lineups_by_artist: dict[int, list[ArtistLineUp]] = {row["id"]: [] for row in basic_info}
    for row in lineup_rows:
        artist_id = row["artist_id"]
        lineups = lineups_by_artist.get(artist_id)
        if lineups is None:
            raise CatalogLoadError(
                "Artist database extract failed: lineUpsMembers references "
                f"unknown artist {artist_id}"
            )
        if row["line_up_id"] != len(lineups):
            raise CatalogLoadError(
                f"Artist database extract failed: line-up index gap for artist {artist_id}"
            )
        lineups.append(
            ArtistLineUp(
                line_up_type=row["line_up_type"],
                members=_parse_credits(
                    row["members"],
                    row["members_line_up"],
                    context=f"artist {artist_id} lineup {row['line_up_id']} members",
                ),
            )
        )

    artists: dict[int, ArtistEntry] = {}
    # Preserve name-resolution order while joining independently read tables by ID.
    for row in basic_info:
        artist_id = row["id"]
        groups = groups_by_artist.get(artist_id)
        if groups is None:
            raise CatalogLoadError(
                "Artist database extract failed: artistsNames/artistsGroups "
                f"missing group membership row for artist {artist_id}"
            )
        artists[artist_id] = ArtistEntry(
            names=tuple(row["romaji_names"].split("\\$")),
            original_names=_original_names(row["original_names"]),
            groups=_parse_credits(
                groups["groups"], groups["groups_line_up"], context=f"artist {artist_id} groups"
            ),
            line_ups=tuple(lineups_by_artist[artist_id]),
            disambiguation=row["disambiguation"],
            type=row["type"],
        )
    return artists


def _original_name(value: str | None) -> str | None:
    """Ignore empty source fields and the literal null placeholder."""
    if value is None:
        return None
    value = value.strip()
    return value if value and value.lower() != "null" else None


def _original_names(value: str | None) -> tuple[str, ...]:
    """Decode independently aggregated original names; preserve spelling order."""
    names = (_original_name(part) for part in (value or "").split("\\$"))
    return tuple(dict.fromkeys(name for name in names if name is not None))


def _parse_credits(ids: str | None, lineups: str | None, *, context: str) -> Credits:
    """Decode parallel columns; reject incomplete lists and invalid lineup sentinels."""
    if not ids and not lineups:
        return ()
    if not ids or not lineups:
        raise CatalogLoadError(f"{context}: missing parallel credit ID/lineup column")
    try:
        credits = tuple(
            (int(person), int(lineup))
            for person, lineup in zip(ids.split(","), lineups.split(","), strict=True)
        )
        if any(lineup < -1 for _, lineup in credits):
            raise ValueError("lineup indexes must be -1 or nonnegative")
        return credits
    except ValueError as error:
        raise CatalogLoadError(f"{context}: invalid credit ID/lineup columns ({error})") from error


def _decode_song(row: sqlite3.Row) -> Song:
    return Song(
        ann_id=row["annId"],
        mal_id=row["malId"],
        anidb_id=row["anidbId"],
        anilist_id=row["anilistId"],
        kitsu_id=row["kitsuId"],
        original_jp_name=_original_name(row["originalJPName"]),
        anime_jp_name=row["animeJPName"],
        anime_en_name=row["animeENName"],
        original_alt_names=_original_names(row["original_alt_names"]),
        romaji_alt_names=(
            tuple(row["romaji_alt_names"].split("\\$")) if row["romaji_alt_names"] else ()
        ),
        anime_vintage=row["animeVintage"],
        anime_type=row["animeType"],
        anime_category=row["animeCategory"],
        song_id=row["songId"],
        ann_song_id=row["annSongId"],
        amq_song_id=row["amqSongId"],
        song_type=row["songType"],
        song_number=row["songNumber"],
        song_category=row["songCategory"],
        original_song_name=_original_name(row["originalSongName"]),
        romaji_song_name=row["romajiSongName"],
        original_song_artist=_original_name(row["originalSongArtist"]),
        romaji_song_artist=row["romajiSongArtist"],
        artists=_parse_credits(
            row["artists"], row["artists_line_up"], context=f"song {row['songId']} artists"
        ),
        original_song_composer=_original_name(row["originalSongComposer"]),
        romaji_song_composer=row["romajiSongComposer"],
        composers=_parse_credits(
            row["composers"], row["composers_line_up"], context=f"song {row['songId']} composers"
        ),
        original_song_arranger=_original_name(row["originalSongArranger"]),
        romaji_song_arranger=row["romajiSongArranger"],
        arrangers=_parse_credits(
            row["arrangers"], row["arrangers_line_up"], context=f"song {row['songId']} arrangers"
        ),
        song_difficulty=row["songDifficulty"],
        is_dub=row["isDub"],
        is_rebroadcast=row["isRebroadcast"],
        song_length=row["songLength"],
        hq=row["HQ"],
        mq=row["MQ"],
        audio=row["audio"],
    )
