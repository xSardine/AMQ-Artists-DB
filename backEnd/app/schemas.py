"""Public API request and response models."""

from pydantic import BaseModel, ConfigDict, Field

MAX_TEXT_FIELD_LENGTH = 500


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


class ArtistSearchFilter(TextSearchFilter):
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

    # Min line-up members required on the song (0 = at least one). Above 0 also finds member credits
    group_granularity: int = Field(0, ge=0)
    # Max other performers on the song besides the match
    max_other_artist: int = Field(99, ge=0)


class ComposerSearchFilter(TextSearchFilter):
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

    # Same as ArtistSearchFilter
    group_granularity: int = Field(0, ge=0)
    max_other_artist: int = Field(99, ge=0)
    # Match arranger credits too, not only composer
    arrangement: bool = True


class SongFilterOptions(BaseModel):
    # Song type filters
    opening_filter: bool = True
    ending_filter: bool = True
    insert_filter: bool = True

    # Broadcast type filters
    normal_broadcast: bool = True
    dub: bool = True
    rebroadcast: bool = True

    # Song category filters
    standard: bool = True
    instrumental: bool = True
    chanting: bool = True
    character: bool = True

    # Anime type filters
    tv_filter: bool = True
    movie_filter: bool = True
    ova_filter: bool = True
    ona_filter: bool = True
    special_filter: bool = True
    doujin_filter: bool = True


class SearchRequest(SongFilterOptions):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "anime_search_filter": {
                    "search": "White Album",
                    "partial_match": True,
                },
                "artist_search_filter": {
                    "search": "Madoka Yonezawa",
                    "partial_match": True,
                    "group_granularity": 0,
                    "max_other_artist": 99,
                },
            }
        }
    )

    anime_search_filter: TextSearchFilter | None = None
    song_name_search_filter: TextSearchFilter | None = None
    artist_search_filter: ArtistSearchFilter | None = None
    composer_search_filter: ComposerSearchFilter | None = None
    and_logic: bool = True
    ignore_duplicate: bool = False


class ArtistIdSearchRequest(SongFilterOptions):
    artist_ids: list[int] = Field(default_factory=list)
    group_granularity: int = Field(0, ge=0)
    max_other_artist: int = Field(99, ge=0)
    ignore_duplicate: bool = False


class ComposerIdSearchRequest(SongFilterOptions):
    composer_ids: list[int] = Field(default_factory=list)
    arrangement: bool = True
    group_granularity: int = Field(0, ge=0)
    max_other_artist: int = Field(99, ge=0)
    ignore_duplicate: bool = False


class AnnIdSearchRequest(SongFilterOptions):
    annId: int
    ignore_duplicate: bool = False


class AnnIdsSearchRequest(SongFilterOptions):
    ann_ids: list[int] = Field(default_factory=list)
    ignore_duplicate: bool = False


class MalIdsSearchRequest(SongFilterOptions):
    mal_ids: list[int] = Field(default_factory=list)
    ignore_duplicate: bool = False


class AnnSongIdsSearchRequest(SongFilterOptions):
    ann_song_ids: list[int] = Field(default_factory=list)
    ignore_duplicate: bool = False


class AmqSongIdsSearchRequest(SongFilterOptions):
    amq_song_ids: list[int] = Field(default_factory=list)
    ignore_duplicate: bool = False


class SeasonSearchRequest(SongFilterOptions):
    season: str = Field(..., max_length=MAX_TEXT_FIELD_LENGTH)
    ignore_duplicate: bool = False


class GetNSongsRequest(SongFilterOptions):
    model_config = ConfigDict(json_schema_extra={"example": {"n": 50}})

    n: int = Field(..., ge=1, le=500)


class Artist(BaseModel):
    id: int
    names: list[str]
    line_up_id: int = -1
    groups: list["Artist"] | None = None
    members: list["Artist"] | None = None


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


class DatabaseTotals(BaseModel):
    total_songs: int
    total_anime: int
    total_artists: int
    total_seasons: int
    links_by_type: dict[str, int]
    songs_by_type: dict[str, int]
    songs_by_broadcast: dict[str, int]
    songs_by_category: dict[str, int]
    songs_by_anime_type: dict[str, int]


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
