"""Typed search criteria and shared request options."""

from dataclasses import dataclass, field
from typing import Literal

from search.filters import SongFilters

IdMatch = Literal["any", "all"]


@dataclass(frozen=True)
class TextSearchFilter:
    search: str
    partial_match: bool = True
    match_case: bool = False


@dataclass(frozen=True, kw_only=True)
class CreditSearchOptions:
    group_granularity: int = 0
    max_other_artist: int = 99


@dataclass(frozen=True)
class ArtistSearchFilter(TextSearchFilter, CreditSearchOptions):
    pass


@dataclass(frozen=True)
class ComposerSearchFilter(ArtistSearchFilter):
    arrangement: bool = True


@dataclass(frozen=True)
class TextCriteria:
    anime: TextSearchFilter | None = None
    song_name: TextSearchFilter | None = None
    artist: ArtistSearchFilter | None = None
    composer: ComposerSearchFilter | None = None
    and_logic: bool = True


ExternalIdSource = Literal["ann", "mal", "anilist", "kitsu", "anidb", "ann-song", "amq-song"]


@dataclass(frozen=True)
class ExternalIdCriteria:
    source: ExternalIdSource
    ids: tuple[int, ...]


@dataclass(frozen=True)
class ArtistIdCriteria:
    ids: tuple[int, ...]
    options: CreditSearchOptions = field(default_factory=CreditSearchOptions)
    id_match: IdMatch = "any"


@dataclass(frozen=True)
class ComposerIdCriteria:
    ids: tuple[int, ...]
    options: CreditSearchOptions = field(default_factory=CreditSearchOptions)
    arrangement: bool = True
    id_match: IdMatch = "any"


@dataclass(frozen=True)
class SeasonCriteria:
    season: str


@dataclass(frozen=True)
class RandomCriteria:
    count: int


SearchCriteria = (
    TextCriteria
    | ExternalIdCriteria
    | ArtistIdCriteria
    | ComposerIdCriteria
    | SeasonCriteria
    | RandomCriteria
)


@dataclass(frozen=True)
class SearchQuery:
    criteria: SearchCriteria
    filters: SongFilters = field(default_factory=SongFilters)
    ignore_duplicate: bool = False
    limit: int | None = None
