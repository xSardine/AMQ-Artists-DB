"""HTTP endpoints; search and catalog rules live in their own packages."""

from fastapi import APIRouter, HTTPException, Query, Request
from api.dependencies import CatalogDependency, CachedResponsesDependency, StatsDependency
from catalog.models import Catalog

from api import log_events
from api.presenters import FormattedSong, format_songs
from api.query_adapter import to_search_query
from api.ranked import get_ranked_time_info, is_ranked_time
from api.log_request_handling import reject_request
from api.response_cache import gzip_json_response
from api.schemas import (
    AmqSongIdsSearchRequest,
    AnnIdLinkedAnimeEntry,
    AnidbIdsSearchRequest,
    AnilistIdsSearchRequest,
    KitsuIdsSearchRequest,
    AnnIdSearchRequest,
    AnnIdsSearchRequest,
    AnnSongIdsSearchRequest,
    ArtistIdSearchRequest,
    ComposerIdSearchRequest,
    SongSelectionRequest,
    DatabaseStats,
    GetNSongsRequest,
    MAX_TEXT_FIELD_LENGTH,
    MalIdsSearchRequest,
    RankedTimeStatus,
    SearchRequest,
    SeasonSearchRequest,
    SongEntry,
)
from search import engine
from search.models import RandomCriteria, SearchQuery
from search.text_matching import has_search_text

router = APIRouter()


def _search_response(request: Request, query: SongSelectionRequest, catalog: Catalog) -> list[FormattedSong]:
    try:
        search_query = to_search_query(query, catalog)
    except HTTPException as error:
        if isinstance(query, SeasonSearchRequest) and error.status_code == 400:
            reject_request(
                request, query, status_code=400, reason="Invalid season", detail=error.detail
            )
        raise
    songs = engine.search_songs(catalog, search_query)
    log_events.record_request(request.url.path, query, request, result_count=len(songs))
    return format_songs(catalog, songs)


# Return 50 random songs, no filters applied, legacy endpoint called on front end page load, do not log
@router.post("/api/get_50_random_songs", response_model=list[SongEntry])
def get_50_random_songs(catalog: CatalogDependency):
    songs = engine.search_songs(catalog, SearchQuery(RandomCriteria(50)))
    return format_songs(catalog, songs)


# Return n random songs
@router.post("/api/get_n_random_songs", response_model=list[SongEntry])
def get_n_random_songs(query: GetNSongsRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a search request
@router.post(
    "/api/search_request",
    response_model=list[SongEntry],
    responses={
        503: {"description": "Song name/artist/composer text search is disabled during ranked time"}
    },
)
def search_request(query: SearchRequest, request: Request, catalog: CatalogDependency):
    # During ranked, song name / artist / composer text search is disabled.
    if is_ranked_time() and (
        has_search_text(query.song_name_search_filter)
        or has_search_text(query.artist_search_filter)
        or has_search_text(query.composer_search_filter)
    ):
        reject_request(
            request,
            query,
            status_code=503,
            reason="Disabled during ranked",
            detail="Song name/artist/composer text search is disabled during ranked time",
        )

    return _search_response(request, query, catalog)


# Return songs from a list of artist IDs
@router.post("/api/artist_ids_request", response_model=list[SongEntry])
def artist_ids_request(query: ArtistIdSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of composer IDs
@router.post("/api/composer_ids_request", response_model=list[SongEntry])
def composer_ids_request(query: ComposerIdSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a single ANN ID (keep this, older clients still request it)
@router.post("/api/annId_request", response_model=list[SongEntry], deprecated=True)
def annId_request(query: AnnIdSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of ANN IDs
@router.post("/api/ann_ids_request", response_model=list[SongEntry])
def ann_ids_request(query: AnnIdsSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of MAL IDs
@router.post("/api/mal_ids_request", response_model=list[SongEntry])
def mal_ids_request(query: MalIdsSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of AniList IDs
@router.post("/api/anilist_ids_request", response_model=list[SongEntry])
def anilist_ids_request(query: AnilistIdsSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of Kitsu IDs
@router.post("/api/kitsu_ids_request", response_model=list[SongEntry])
def kitsu_ids_request(query: KitsuIdsSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of AniDB IDs
@router.post("/api/anidb_ids_request", response_model=list[SongEntry])
def anidb_ids_request(query: AnidbIdsSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of ANN song IDs
@router.post("/api/ann_song_ids_request", response_model=list[SongEntry])
def ann_song_ids_request(query: AnnSongIdsSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return songs from a list of AMQ song IDs
@router.post("/api/amq_song_ids_request", response_model=list[SongEntry])
def amq_song_ids_request( query: AmqSongIdsSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


# Return all songs from a specific season
@router.post("/api/season_request", response_model=list[SongEntry])
def season_request(query: SeasonSearchRequest, request: Request, catalog: CatalogDependency):
    return _search_response(request, query, catalog)


@router.get("/api/genres", response_model=list[str])
def get_genres(catalog: CatalogDependency):
    return sorted(catalog.genre_by_lower.values(), key=str.casefold)


@router.get("/api/tags", response_model=list[str])
def get_tags(catalog: CatalogDependency):
    return sorted(catalog.tag_by_lower.values(), key=str.casefold)


# Return every possible songartist string for autocompletion
@router.get("/api/artist_autocomplete", response_model=list[str])
def artist_autocomplete(
    catalog: CatalogDependency,
    search: str | None = Query(
        None,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Case-insensitive partial match on romaji artist name.",
    ),
    count: int = Query(
        99999,
        ge=1,
        description="Maximum number of suggestions to return.",
    ),
):
    return engine.autocomplete_artists(catalog, search, count)


# Return every possible anime song name string for autocompletion
@router.get("/api/song_name_autocomplete", response_model=list[str])
def song_name_autocomplete(
    catalog: CatalogDependency,
    search: str | None = Query(
        None,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Case-insensitive partial match on romaji song name.",
    ),
    count: int = Query(
        99999,
        ge=1,
        description="Maximum number of suggestions to return.",
    ),
):
    return engine.autocomplete_song_names(catalog, search, count)


# Return every possible anime name string for autocompletion with possible filters on song_name and artist
@router.get("/api/anime_name_autocomplete", response_model=list[str])
def anime_name_autocomplete(
    catalog: CatalogDependency,
    songName: str | None = Query(
        None,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Filter to anime that have this romaji song name.",
    ),
    songArtist: str | None = Query(
        None,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Filter to anime that have this romaji song artist.",
    ),
):
    return engine.autocomplete_anime_names(catalog, songName, songArtist)


@router.get("/api/catalog_dump", include_in_schema=False)
def catalog_dump(request: Request, cached: CachedResponsesDependency):
    return gzip_json_response(request, cached.catalog_dump)


# Return a .json dict containing every key annId value linked_ids
@router.get("/api/annid_linked_ids", response_model=dict[int, AnnIdLinkedAnimeEntry], response_model_by_alias=False)
def annid_linked_ids(request: Request, cached: CachedResponsesDependency):
    return gzip_json_response(request, cached.annid_linked_ids)


# Return information about ranked restrictions
@router.get("/api/ranked_time_status", response_model=RankedTimeStatus)
async def get_ranked_time_status():
    return get_ranked_time_info()


# Return stats and song counts to monitor the DB
@router.get("/api/database_stats", response_model=DatabaseStats)
def get_database_stats(stats: StatsDependency):
    return stats
