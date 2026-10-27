"""Immutable catalog records, relationship types, and the read catalog container."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from catalog.credits import CreditGraph

CreditPair = tuple[int, int]
Credits = tuple[CreditPair, ...]


class SearchName(NamedTuple):
    """A searchable spelling with its case-insensitive form prepared at startup."""

    value: str
    lowered: str


@dataclass(frozen=True, slots=True)
class Song:
    ann_id: int
    mal_id: int | None
    anidb_id: int | None
    anilist_id: int | None
    kitsu_id: int | None
    original_jp_name: str | None
    anime_jp_name: str | None
    anime_en_name: str | None
    original_alt_names: tuple[str, ...]
    romaji_alt_names: tuple[str, ...]
    anime_vintage: str | None
    anime_type: str | None
    anime_category: str | None
    song_id: int
    ann_song_id: int | None
    amq_song_id: int | None
    song_type: int
    song_number: int
    song_category: str | None
    original_song_name: str | None
    romaji_song_name: str
    original_song_artist: str | None
    romaji_song_artist: str | None
    artists: Credits
    original_song_composer: str | None
    romaji_song_composer: str | None
    composers: Credits
    original_song_arranger: str | None
    romaji_song_arranger: str | None
    arrangers: Credits
    song_difficulty: float | None
    is_dub: int | None
    is_rebroadcast: int | None
    song_length: float | None
    hq: str | None
    mq: str | None
    audio: str | None

    @property
    def has_difficulty(self) -> bool:
        return self.song_difficulty is not None and self.song_difficulty > 0

    @property
    def available_media_links(self) -> frozenset[str]:
        return frozenset(
            kind for kind, link in (("hq", self.hq), ("mq", self.mq), ("audio", self.audio)) if link
        )


SongMap = dict[int, Song]

LineUpType = Literal["vocalists", "composers"]
ArtistType = Literal["person", "group", "choir"]


@dataclass(frozen=True, slots=True)
class ArtistLineUp:
    line_up_type: LineUpType
    members: Credits


@dataclass(frozen=True, slots=True)
class ArtistEntry:
    names: tuple[str, ...]
    groups: Credits
    line_ups: tuple[ArtistLineUp, ...]
    disambiguation: str | None
    type: ArtistType
    original_names: tuple[str, ...] = ()
    ann_id: int | None = None
    mal_id: int | None = None
    anilist_id: int | None = None


ArtistDatabase = Mapping[int, ArtistEntry]
ArtistNameRows = tuple[tuple[int, SearchName], ...]


@dataclass(frozen=True, slots=True)
class AnimeCatalogEntry:
    anime_jp_name: str | None
    anime_en_name: str | None
    anime_alt_names: tuple[str, ...]
    anime_vintage: str | None
    anime_type: str | None
    anime_category: str | None
    songs: tuple[Song, ...]
    search_names: tuple[SearchName, ...]


AnimeDatabase = Mapping[int, AnimeCatalogEntry]
SongRowsByExternalId = Mapping[int, tuple[Song, ...]]  # external ID -> rows
SongIdReverseMap = Mapping[int, tuple[int, ...]]  # credited artist/composer ID -> songs.id
AnimeLabelsByAnnId = Mapping[int, frozenset[str]]  # annId -> genres or tags
LabelCanonicalMap = Mapping[str, str]  # lowercased label -> DB spelling


class CatalogLoadError(RuntimeError):
    """Raised when catalog source data cannot be read or validated."""


@dataclass(frozen=True)
class Catalog:
    song_rows: tuple[Song, ...]
    songs_by_id: Mapping[int, Song]
    anime_by_id: AnimeDatabase
    artists_by_id: ArtistDatabase
    artist_name_rows: ArtistNameRows
    songs_by_artist_id: SongIdReverseMap
    songs_by_composer_id: SongIdReverseMap
    songs_by_arranger_id: SongIdReverseMap
    songs_by_ann_id: SongRowsByExternalId
    songs_by_mal_id: SongRowsByExternalId
    songs_by_anilist_id: SongRowsByExternalId
    songs_by_kitsu_id: SongRowsByExternalId
    songs_by_anidb_id: SongRowsByExternalId
    songs_by_ann_song_id: SongRowsByExternalId
    songs_by_amq_song_id: SongRowsByExternalId
    songs_by_season: Mapping[str, tuple[Song, ...]]
    genres_by_ann_id: AnimeLabelsByAnnId
    tags_by_ann_id: AnimeLabelsByAnnId
    genre_by_lower: LabelCanonicalMap
    tag_by_lower: LabelCanonicalMap
    artist_autocomplete_values: tuple[SearchName, ...]
    song_name_autocomplete_values: tuple[SearchName, ...]
    credits: CreditGraph
    database_updated_at: str | None = None
