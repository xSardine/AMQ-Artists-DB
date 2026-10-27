"""Public API request and response models."""

from collections.abc import Iterable
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

MAX_TEXT_FIELD_LENGTH = 500
SearchIdList = Annotated[list[int], Field(min_length=1, max_length=500)]
SEASON_REGEX = r"^(Winter|Spring|Summer|Fall) \d{4}$"
EMPTY_FILTER_MESSAGES = {
    "song_types": "At least one song type filter (opening, ending, insert) must be enabled.",
    "broadcasts": "At least one broadcast type filter (normal, dub, rebroadcast) must be enabled.",
    "song_categories": "At least one performance filter (standard, character, chanting, instrumental, other) must be enabled.",
    "anime_types": "At least one anime type filter (tv, movie, ova, ona, special, other) must be enabled.",
}


def validate_requirements(
    require_any: Iterable[str],
    require_all: Iterable[str],
    exclude: Iterable[str],
    kind: str,
) -> None:
    """Reject contradictory membership rules, including after catalog canonicalization."""
    required_any = set(require_any)
    required_all = set(require_all)
    excluded = set(exclude)
    if required_all & excluded:
        raise ValueError(f"A {kind} cannot be both required and excluded.")
    if required_any and required_any <= excluded:
        raise ValueError(f"At least one require_any {kind} must not be excluded.")


class TextSearchFilter(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "search": "White Album",
                "partial_match": True,
                "match_case": False,
            }
        }
    )

    search: str = Field(..., max_length=MAX_TEXT_FIELD_LENGTH)
    partial_match: bool = True
    match_case: bool = False


class CreditSearchOptions(BaseModel):
    # Minimum distinct expanded members, capped at each lineup's expanded size.
    # 0 still requires an overlap; values above 0 also find member credits.
    group_granularity: int = Field(0, ge=0)
    # Max other performers on the song besides the match
    max_other_artist: int = Field(99, ge=0)


class ArtistSearchFilter(TextSearchFilter, CreditSearchOptions):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "search": "fripSide",
                "partial_match": True,
                "match_case": False,
                "group_granularity": 1,
                "max_other_artist": 2,
            }
        }
    )


class ComposerSearchFilter(ArtistSearchFilter):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "search": "Hiroyuki Sawano",
                "partial_match": True,
                "match_case": False,
                "group_granularity": 0,
                "max_other_artist": 99,
                "arrangement": True,
            }
        }
    )

    # Match arranger credits too, not only composer
    arrangement: bool = True


LinkType = Literal["audio", "mq", "hq"]
SongType = Literal["opening", "ending", "insert"]
BroadcastType = Literal["normal", "dub", "rebroadcast"]
SongCategory = Literal["standard", "character", "chanting", "instrumental", "other"]
AnimeType = Literal["tv", "movie", "ova", "ona", "special", "other"]


class MediaLinksFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_any: list[LinkType] = Field(default_factory=list)
    require_all: list[LinkType] = Field(default_factory=list)
    exclude: list[LinkType] = Field(default_factory=list)

    @field_validator("require_any", "require_all", "exclude", mode="before")
    @classmethod
    def normalize_link_types(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            return value
        return [item.lower() if isinstance(item, str) else item for item in value]

    @model_validator(mode="after")
    def reject_impossible_requirements(self):
        validate_requirements(self.require_any, self.require_all, self.exclude, "link type")
        return self


class AnimeLabelsFilter(BaseModel):
    """Optional anime genre/tag filter using the same operators as media_links."""

    model_config = ConfigDict(extra="forbid")

    require_any: list[str] = Field(default_factory=list, max_length=100)
    require_all: list[str] = Field(default_factory=list, max_length=100)
    exclude: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("require_any", "require_all", "exclude", mode="before")
    @classmethod
    def normalize_labels(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            return value
        return [item.strip() if isinstance(item, str) else item for item in value]

    @field_validator("require_any", "require_all", "exclude")
    @classmethod
    def reject_blank_or_long_labels(cls, value):
        for item in value:
            if not isinstance(item, str) or not item:
                raise ValueError("Each label must be a non-empty string.")
            if len(item) > MAX_TEXT_FIELD_LENGTH:
                raise ValueError(
                    f"Each label must be at most {MAX_TEXT_FIELD_LENGTH} characters."
                )
        return value

    @model_validator(mode="after")
    def reject_impossible_requirements(self):
        validate_requirements(self.require_any, self.require_all, self.exclude, "label")
        return self


class SeasonFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: str | None = Field(None, max_length=11, pattern=SEASON_REGEX)
    end: str | None = Field(None, max_length=11, pattern=SEASON_REGEX)

    @model_validator(mode="after")
    def require_at_least_one_bound(self):
        if self.start is None and self.end is None:
            raise ValueError("A season range requires a start or end value.")
        return self


class DifficultyFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: float | None = Field(None, ge=0, le=100)
    end: float | None = Field(None, ge=0, le=100)
    include_no_difficulty: bool = False

    @model_validator(mode="after")
    def require_at_least_one_condition(self):
        if self.start is None and self.end is None and not self.include_no_difficulty:
            raise ValueError(
                "A difficulty filter requires a start, end, or include_no_difficulty."
            )
        return self


class SongLengthFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Song duration in seconds. Bounds are inclusive.
    start: float | None = Field(None, ge=0)
    end: float | None = Field(None, ge=0)
    include_no_length: bool = False

    @model_validator(mode="after")
    def require_at_least_one_condition(self):
        if self.start is None and self.end is None and not self.include_no_length:
            raise ValueError(
                "A song length filter requires a start, end, or include_no_length."
            )
        return self


class SongFilterOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    song_types: list[SongType] = Field(
        default_factory=lambda: ["opening", "ending", "insert"],
        min_length=1,
    )
    broadcasts: list[BroadcastType] = Field(
        default_factory=lambda: ["normal", "dub", "rebroadcast"],
        min_length=1,
    )
    song_categories: list[SongCategory] = Field(
        default_factory=lambda: ["standard", "character", "chanting", "instrumental", "other"],
        min_length=1,
    )
    anime_types: list[AnimeType] = Field(
        default_factory=lambda: ["tv", "movie", "ova", "ona", "special", "other"],
        min_length=1,
    )
    season: SeasonFilter | None = None
    difficulty: DifficultyFilter | None = None
    song_length: SongLengthFilter | None = None
    media_links: MediaLinksFilter | None = None
    genres: AnimeLabelsFilter | None = None
    tags: AnimeLabelsFilter | None = None

    @field_validator("song_types", "broadcasts", "song_categories", "anime_types", mode="before")
    @classmethod
    def require_filter_selection(cls, value, info):
        if isinstance(value, list) and not value:
            raise PydanticCustomError(
                f"empty_{info.field_name}",
                EMPTY_FILTER_MESSAGES[info.field_name],
            )
        return value


class FilteredRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filters: SongFilterOptions = Field(default_factory=SongFilterOptions)


class SongSelectionRequest(FilteredRequest):
    ignore_duplicate: bool = False


class SearchRequest(SongSelectionRequest):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "anime_search_filter": {
                    "search": "White Album",
                    "partial_match": True,
                    "match_case": False,
                },
                "artist_search_filter": {
                    "search": "Madoka Yonezawa",
                    "partial_match": True,
                    "match_case": False,
                    "group_granularity": 0,
                    "max_other_artist": 99,
                },
                "filters": {
                    "song_types": ["opening", "ending"],
                    "broadcasts": ["normal"],
                    "song_categories": ["standard"],
                    "anime_types": ["tv"],
                    "season": {
                        "start": "Winter 2020",
                        "end": "Fall 2024",
                    },
                    "difficulty": {
                        "start": 40,
                        "end": 80,
                        "include_no_difficulty": False,
                    },
                    "song_length": {
                        "start": 60,
                        "end": 120,
                        "include_no_length": False,
                    },
                    "media_links": {
                        "require_any": ["audio", "mq"],
                        "require_all": [],
                        "exclude": ["hq"],
                    },
                    "genres": {
                        "require_any": ["Action", "Comedy"],
                        "require_all": [],
                        "exclude": ["Ecchi"],
                    },
                    "tags": {
                        "require_any": ["School"],
                        "require_all": [],
                        "exclude": [],
                    },
                },
            }
        }
    )

    anime_search_filter: TextSearchFilter | None = None
    song_name_search_filter: TextSearchFilter | None = None
    artist_search_filter: ArtistSearchFilter | None = None
    composer_search_filter: ComposerSearchFilter | None = None
    and_logic: bool = True

    @model_validator(mode="after")
    def require_search_text(self):
        search_filters = (
            self.anime_search_filter,
            self.song_name_search_filter,
            self.artist_search_filter,
            self.composer_search_filter,
        )
        if not any(search_filter and search_filter.search.strip() for search_filter in search_filters):
            raise ValueError("At least one non-empty text search filter is required.")
        return self


class ArtistIdSearchRequest(SongSelectionRequest, CreditSearchOptions):
    artist_ids: SearchIdList
    id_match: Literal["any", "all"] = "any"


class ComposerIdSearchRequest(SongSelectionRequest, CreditSearchOptions):
    composer_ids: SearchIdList
    arrangement: bool = True
    id_match: Literal["any", "all"] = "any"


class AnnIdSearchRequest(SongSelectionRequest):
    annId: int


class AnnIdsSearchRequest(SongSelectionRequest):
    ann_ids: SearchIdList


class MalIdsSearchRequest(SongSelectionRequest):
    mal_ids: SearchIdList


class AnilistIdsSearchRequest(SongSelectionRequest):
    anilist_ids: SearchIdList


class KitsuIdsSearchRequest(SongSelectionRequest):
    kitsu_ids: SearchIdList


class AnidbIdsSearchRequest(SongSelectionRequest):
    anidb_ids: SearchIdList


class AnnSongIdsSearchRequest(SongSelectionRequest):
    ann_song_ids: SearchIdList


class AmqSongIdsSearchRequest(SongSelectionRequest):
    amq_song_ids: SearchIdList


class SeasonSearchRequest(SongSelectionRequest):
    season: str = Field(..., max_length=MAX_TEXT_FIELD_LENGTH)


class GetNSongsRequest(SongSelectionRequest):
    model_config = ConfigDict(json_schema_extra={"example": {"n": 50}})

    n: int = Field(..., ge=1, le=500)


class Artist(BaseModel):
    id: int
    names: list[str]
    line_up_id: int = -1
    groups: list["Artist"] | None = None
    members: list["Artist"] | None = None
    type: Literal["person", "group", "choir"] | None = None
    # Direct members of the credited lineup. For a group credited without a
    # specific lineup, distinct members across its lineups.
    member_count: int | None = None


Artist.model_rebuild()


class AnimeListLinks(BaseModel):
    myanimelist: int | None = None
    anidb: int | None = None
    anilist: int | None = None
    kitsu: int | None = None


class SongEntry(BaseModel):
    annId: int
    annSongId: int
    amqSongId: int
    animeENName: str
    animeJPName: str
    animeAltName: list[str]
    animeVintage: str | None = None
    linked_ids: AnimeListLinks
    animeType: str | None = None
    animeCategory: str | None = None
    songType: str
    songName: str
    songArtist: str
    songComposer: str
    songArranger: str
    songDifficulty: float | None = None
    songCategory: str | None = None
    songLength: float | None = None
    isDub: bool | None = None
    isRebroadcast: bool | None = None
    HQ: str | None = None
    MQ: str | None = None
    audio: str | None = None
    artists: list[Artist]
    composers: list[Artist]
    arrangers: list[Artist]


class DatabaseStatsMissingData(BaseModel):
    songs_without_difficulty: int
    songs_without_length: int
    songs_without_season: int
    songs_without_genre: int
    songs_without_tag: int
    songs_without_links: int
    anime_without_genre: int
    anime_without_tag: int
    anime_without_season: int


class DatabaseStatsCoverage(BaseModel):
    present: int
    total: int


class CreditGapStatistics(BaseModel):
    text_without_ids: int
    no_text_or_ids: int


class CreditRoleStatistics(BaseModel):
    songs_with_ids: int
    text_without_ids: int
    no_text_or_ids: int
    unique_direct_ids: int
    direct_people: int
    lineup_only_people: int
    all_identified_people: int
    specific_group_lineup_songs: int
    unspecified_group_lineup_songs: int
    songs_by_id_count: dict[str, int]
    missing_ids_by_performance: dict[str, CreditGapStatistics]


class ArtistGroupStatistics(BaseModel):
    total: int
    by_lineup_type: dict[str, int]
    by_lineup_count: dict[str, int]
    lineups_by_type: dict[str, int]
    nested_groups: int


class MostCreditedArtist(BaseModel):
    id: int
    name: str
    type: str | None
    disambiguation: str | None
    unique_songs: int
    anime_count: int


class ArtistCreditStatistics(BaseModel):
    types: dict[str, int]
    directly_credited: int
    roster_only: int
    other_catalog_entries: int
    role_combinations: dict[str, int]
    aliases: dict[str, int]
    groups: ArtistGroupStatistics
    roles: dict[str, CreditRoleStatistics]
    artists_by_unique_song_count: dict[str, int]
    most_credited: dict[str, list[MostCreditedArtist]]


class MeasurementSummary(BaseModel):
    known: int
    mean: float | None
    median: float | None
    q1: float | None
    q3: float | None


class SongSummary(BaseModel):
    songs: int
    anime: int
    song_types: dict[str, int]
    difficulty: MeasurementSummary
    length: MeasurementSummary
    media: int


class SongDistribution(BaseModel):
    summary: SongSummary
    # Sparse integer-second/guess-rate histograms, matching the existing bucket rules.
    difficulty: dict[str, int]
    length: dict[str, int]


class PeriodStatistics(BaseModel):
    overall: SongSummary
    song_type: dict[str, SongSummary]
    anime_format: dict[str, SongSummary]


class TopAnime(BaseModel):
    ann_id: int
    name: str
    songs: int
    song_types: dict[str, int]


class AnimeSongStatistics(BaseModel):
    anime: int
    distribution: dict[str, int]
    median: float | None
    p90: float | None
    maximum: int | None
    most_songs: list[TopAnime]


class SongAnalysis(BaseModel):
    distributions: dict[str, dict[str, SongDistribution]]
    seasons: dict[str, PeriodStatistics]
    years: dict[str, PeriodStatistics]
    songs_per_anime: dict[str, AnimeSongStatistics]
    genres: dict[str, SongSummary]
    tags: dict[str, SongSummary]


class DatabaseStats(BaseModel):
    # UTC timestamp written when the SQLite database was generated.
    database_updated_at: str | None = None
    total_songs: int
    # Distinct positive AMQ song IDs; songs without an AMQ ID are excluded.
    total_unique_amq_songs: int
    total_anime: int
    total_artists: int
    total_seasons: int
    links_by_type: dict[str, int]
    # Overlapping coverage totals for any video, all three formats, and no media.
    links_by_coverage: dict[str, int]
    # Mutually exclusive combinations, ordered with HQ + MQ + audio first.
    links_by_combination: dict[str, int]
    songs_by_type: dict[str, int]
    songs_by_broadcast: dict[str, int]
    songs_by_performance: dict[str, int]
    songs_by_anime_type: dict[str, int]
    # Index = difficulty 0..100; missing and nonpositive values are only in missing_data.
    songs_by_difficulty: list[int]
    # Index = floor(songLength) seconds; length of the list is max observed + 1.
    songs_by_length: list[int]
    songs_by_season: dict[str, int]
    songs_by_genre: dict[str, int]
    songs_by_tag: dict[str, int]
    # Map of song-count → number of anime with that many songs (keys are decimal strings).
    songs_per_anime: dict[str, int]
    missing_data: DatabaseStatsMissingData
    original_name_coverage: dict[str, DatabaseStatsCoverage]
    # List-site coverage counts anime; ANN/AMQ song-ID coverage counts song appearances.
    external_id_coverage: dict[str, DatabaseStatsCoverage]
    artist_credits: ArtistCreditStatistics
    song_analysis: SongAnalysis


class AnnIdBulkLinkedIds(BaseModel):
    annId: int
    myanimelist: int | None = None
    anidb: int | None = None
    anilist: int | None = None
    kitsu: int | None = None


class AnnIdLinkedAnimeEntry(BaseModel):
    animeENName: str | None = None
    animeJPName: str | None = None
    animeAltName: list[str]
    linked_ids: AnnIdBulkLinkedIds


class RankedTimeStatus(BaseModel):
    active: bool
    region: str | None = Field(None, description="Central, Western, or Eastern when ranked is active.")
    remaining_minutes: int | None = None
    remaining_seconds: int | None = None
    server_time: str = Field(description="Current server time in UTC (ISO 8601).")
