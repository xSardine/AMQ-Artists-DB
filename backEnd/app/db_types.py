"""Shared runtime types for SQLite rows and the in-memory catalog."""

from typing import Any, Literal, NamedTuple, TypedDict


SongFullRow = tuple[Any, ...]  # 40-column row from SELECT * FROM songsFull
SongMap = dict[int, SongFullRow]  # internal songs.id -> unique row
FormattedSong = dict[str, Any]  # pre-validation payload for schemas.SongEntry


# A credit pair identifies an artist/group and one of its line-ups. A line-up ID
# of -1 means the artist/group is credited directly rather than through a roster.
CreditPair = tuple[int, int]
Credits = tuple[CreditPair, ...]
LineUpType = Literal["vocalists", "composers"]
ArtistType = Literal["person", "group", "choir"]


class ArtistLineUp(TypedDict):
    line_up_type: LineUpType
    members: Credits


class ArtistEntry(TypedDict):
    names: list[str]
    groups: list[CreditPair]
    line_ups: list[ArtistLineUp]
    disambiguation: str | None
    type: ArtistType


ArtistDatabase = dict[str, ArtistEntry]
ArtistNameRows = tuple[tuple[int, str], ...]


class AnimeCatalogEntry(TypedDict):
    animeJPName: str | None
    animeENName: str | None
    animeAltNames: str | None
    animeVintage: str | None
    animeType: str | None
    animeCategory: str | None
    songs: list[SongFullRow]


AnimeDatabase = dict[int, AnimeCatalogEntry]
SongRowsByExternalId = dict[int, tuple[SongFullRow, ...]]  # external ID -> rows
SongIdReverseMap = dict[int, tuple[int, ...]]  # credited artist/composer ID -> songs.id
ArtistIdResolutionCache = dict[tuple[str, bool], list[int]]  # (compiled regex text, case-sensitive flag) -> resolved artist/composer IDs


class DatabaseTotalsPayload(TypedDict):
    total_songs: int
    total_anime: int
    total_artists: int
    total_seasons: int
    links_by_type: dict[str, int]
    songs_by_type: dict[str, int]
    songs_by_broadcast: dict[str, int]
    songs_by_category: dict[str, int]
    songs_by_anime_type: dict[str, int]


class DatabaseQueryError(RuntimeError):
    """Raised when the database cannot be loaded or queried."""


class CreditTarget(NamedTuple):
    """One search-side roster used for artist/composer overlap checks."""

    # The number of immediate roster entries used by the group-granularity rule.
    line_up_len: int
    # The recursively expanded IDs compared with a song's flattened credits.
    members_flat: frozenset[int]


# songsFull column indices
COL_ANN_ID = 0
COL_MAL_ID = 1
COL_ANIDB_ID = 2
COL_ANILIST_ID = 3
COL_KITSU_ID = 4
COL_ORIGINAL_JP_NAME = 5
COL_ANIME_JP_NAME = 6
COL_ANIME_EN_NAME = 7
COL_ORIGINAL_ALT_NAMES = 8
COL_ROMAJI_ALT_NAMES = 9
COL_ANIME_VINTAGE = 10
COL_ANIME_TYPE = 11
COL_ANIME_CATEGORY = 12
COL_SONG_ID = 13
COL_ANN_SONG_ID = 14
COL_AMQ_SONG_ID = 15
COL_SONG_TYPE = 16
COL_SONG_NUMBER = 17
COL_SONG_CATEGORY = 18
COL_ORIGINAL_SONG_NAME = 19
COL_ROMAJI_SONG_NAME = 20
COL_ORIGINAL_SONG_ARTIST = 21
COL_ROMAJI_SONG_ARTIST = 22
COL_ARTISTS = 23
COL_ARTISTS_LINE_UP = 24
COL_ORIGINAL_SONG_COMPOSER = 25
COL_ROMAJI_SONG_COMPOSER = 26
COL_COMPOSERS = 27
COL_COMPOSERS_LINE_UP = 28
COL_ORIGINAL_SONG_ARRANGER = 29
COL_ROMAJI_SONG_ARRANGER = 30
COL_ARRANGERS = 31
COL_ARRANGERS_LINE_UP = 32
COL_SONG_DIFFICULTY = 33
COL_IS_DUB = 34
COL_IS_REBROADCAST = 35
COL_SONG_LENGTH = 36
COL_HQ = 37
COL_MQ = 38
COL_AUDIO = 39
