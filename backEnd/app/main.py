from pathlib import Path
import time

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse

import get_search_result
import request_log
from sql_calls import DatabaseQueryError
import sql_calls
import utils
from song_filters import SongFilters
from schemas import *


def _elapsed_ms(start: float) -> int:
    """Returns the elapsed time in milliseconds since the given start time."""
    return int((time.perf_counter() - start) * 1000)


# Launch API
app = FastAPI()
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Compress responses > 1000 bytes
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Accept requests from any domain
    allow_credentials=True,  # Support cookies/credentials
    allow_methods=["*"],     # Permit all HTTP methods
    allow_headers=["*"],     # Allow any HTTP headers
)


# Handle validation errors from request body
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = exc.body
    if isinstance(body, (bytes, bytearray)):
        try:
            body = body.decode()
        except UnicodeDecodeError:
            body = repr(body)

    request_log.record_request(
        request.url.path,
        body,
        request,
        http_status=422,
        reason="Validation error",
        errors=exc.errors(),
        raise_http_exception=False,
    )
    return await request_validation_exception_handler(request, exc)


# Handle SQLite failures
@app.exception_handler(DatabaseQueryError)
async def database_query_error_handler(request: Request, exc: DatabaseQueryError):
    request_log.record_request(
        request.url.path,
        None,
        request,
        http_status=500,
        reason="SQL failure",
        detail=str(exc),
    )


# Map request booleans to SongFilters; 400 + log if a filter group is empty.
def resolve_song_filters(query, *, endpoint: str, request: Request | None = None) -> SongFilters:
    song_types = []
    if query.opening_filter:
        song_types.append(1)
    if query.ending_filter:
        song_types.append(2)
    if query.insert_filter:
        song_types.append(3)

    if not song_types:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="No song type filters",
            detail="At least one song type filter (opening, ending, or insert) must be enabled.",
        )

    broadcasts = []
    if query.normal_broadcast:
        broadcasts.append("Normal")
    if query.dub:
        broadcasts.append("Dub")
    if query.rebroadcast:
        broadcasts.append("Rebroadcast")

    if not broadcasts:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="No broadcast filters",
            detail="At least one broadcast type filter (normal, dub, or rebroadcast) must be enabled.",
        )

    song_categories = []
    if query.standard:
        song_categories.append("Standard")
        song_categories.append("No Category")
    if query.instrumental:
        song_categories.append("Instrumental")
    if query.chanting:
        song_categories.append("Chanting")
    if query.character:
        song_categories.append("Character")

    if not song_categories:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="No song category filters",
            detail="At least one song category filter (standard, instrumental, chanting, or character) must be enabled.",
        )

    anime_types = []
    if query.tv_filter:
        anime_types.append("TV")
    if query.movie_filter:
        anime_types.append("Movie")
    if query.ova_filter:
        anime_types.append("OVA")
    if query.ona_filter:
        anime_types.append("ONA")
    if query.special_filter:
        anime_types.append("Special")
    if query.doujin_filter:
        anime_types.append("Doujin")

    if not anime_types:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="No anime type filters",
            detail="At least one anime type filter (tv, movie, ova, ona, special, or doujin) must be enabled.",
        )

    return SongFilters(
        song_types=song_types,
        broadcasts=broadcasts,
        song_categories=song_categories,
        anime_types=anime_types,
    )


# Return 50 random songs, no filters applied, legacy endpoint called on front end page load, do not log
@app.post("/api/get_50_random_songs", response_model=list[SongEntry])
async def get_50_random_songs():
    songs = sql_calls.get_random_songs(50)
    artist_database = sql_calls.extract_artist_database()
    song_list = [utils.format_song(artist_database, song) for song in songs]
    return song_list


# Return n random songs
@app.post("/api/get_n_random_songs", response_model=list[SongEntry])
async def get_n_random_songs(query: GetNSongsRequest, request: Request):
    endpoint = "/api/get_n_random_songs"

    if query.n < 1 or query.n > 500:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="Invalid n",
            detail="n must be between 1 and 500",
        )

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)
    start = time.perf_counter()
    songs = sql_calls.get_random_songs(query.n, filters)
    artist_database = sql_calls.extract_artist_database()
    song_list = [utils.format_song(artist_database, song) for song in songs]

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a search request
@app.post(
    "/api/search_request",
    response_model=list[SongEntry],
    responses={503: {"description": "Song name/artist/composer text search is disabled during ranked time"}},
)
async def search_request(query: SearchRequest, request: Request):
    endpoint = "/api/search_request"

    # During ranked, song name / artist / composer text search is disabled.
    if utils.is_ranked_time() and (
        utils.has_search_text(query.song_name_search_filter)
        or utils.has_search_text(query.artist_search_filter)
        or utils.has_search_text(query.composer_search_filter)
    ):
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=503,
            reason="Disabled during ranked",
            detail="Song name/artist/composer text search is disabled during ranked time",
        )

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)
    start = time.perf_counter()
    song_list = get_search_result.get_search_results(
        query.anime_search_filter,
        query.song_name_search_filter,
        query.artist_search_filter,
        query.composer_search_filter,
        query.and_logic,
        query.ignore_duplicate,
        500,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a list of artist IDs
@app.post("/api/artist_ids_request", response_model=list[SongEntry])
async def artist_ids_request(query: ArtistIdSearchRequest, request: Request):
    endpoint = "/api/artist_ids_request"

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)
    start = time.perf_counter()
    song_list = get_search_result.get_artist_ids_song_list(
        query.artist_ids,
        query.max_other_artist,
        query.group_granularity,
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a list of composer IDs
@app.post("/api/composer_ids_request", response_model=list[SongEntry])
async def composer_ids_request(query: ComposerIdSearchRequest, request: Request):
    endpoint = "/api/composer_ids_request"

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)
    start = time.perf_counter()
    song_list = get_search_result.get_composer_ids_song_list(
        query.composer_ids,
        query.arrangement,
        query.group_granularity,
        query.max_other_artist,
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a single anime ANN ID (deprecated)
@app.post("/api/annId_request", response_model=list[SongEntry], deprecated=True)
async def annId_request(query: AnnIdSearchRequest, request: Request):
    endpoint = "/api/annId_request"

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)
    start = time.perf_counter()
    song_list = get_search_result.get_ann_ids_song_list(
        [query.annId],
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a list of anime ANN IDs
@app.post("/api/ann_ids_request", response_model=list[SongEntry])
async def ann_ids_request(query: AnnIdsSearchRequest, request: Request):
    endpoint = "/api/ann_ids_request"

    if len(query.ann_ids) > 500:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="Too many IDs",
            detail="Too many ANN IDs. Maximum allowed is 500.",
        )

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)
    start = time.perf_counter()
    song_list = get_search_result.get_ann_ids_song_list(
        query.ann_ids,
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a list of anime MAL IDs
@app.post("/api/mal_ids_request", response_model=list[SongEntry])
async def mal_ids_request(query: MalIdsSearchRequest, request: Request):
    endpoint = "/api/mal_ids_request"

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)

    if len(query.mal_ids) > 500:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="Too many IDs",
            detail="Too many MAL IDs. Maximum allowed is 500.",
        )

    start = time.perf_counter()
    song_list = get_search_result.get_mal_ids_song_list(
        query.mal_ids,
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a list of ANN song IDs
@app.post("/api/ann_song_ids_request", response_model=list[SongEntry])
async def ann_song_ids_request(query: AnnSongIdsSearchRequest, request: Request):
    endpoint = "/api/ann_song_ids_request"

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)

    if len(query.ann_song_ids) > 500:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="Too many IDs",
            detail="Too many ANN Song IDs. Maximum allowed is 500.",
        )

    start = time.perf_counter()
    song_list = get_search_result.get_ann_song_ids_song_list(
        query.ann_song_ids,
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return songs from a list of AMQ song IDs
@app.post("/api/amq_song_ids_request", response_model=list[SongEntry])
async def amq_song_ids_request(query: AmqSongIdsSearchRequest, request: Request):
    endpoint = "/api/amq_song_ids_request"

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)

    if len(query.amq_song_ids) > 500:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="Too many IDs",
            detail="Too many AMQ Song IDs. Maximum allowed is 500.",
        )

    start = time.perf_counter()
    song_list = get_search_result.get_amq_song_ids_song_list(
        query.amq_song_ids,
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return all songs from a specific season
@app.post("/api/season_request", response_model=list[SongEntry])
async def season_request(query: SeasonSearchRequest, request: Request):
    endpoint = "/api/season_request"

    # Validate season format ("Season YYYY"); normalize whitespace before parsing.
    possible_seasons = ["Winter", "Spring", "Summer", "Fall"]
    season_parts = " ".join(query.season.split()).split(" ")
    error_detail = None

    if len(season_parts) != 2:
        error_detail = "Invalid season format. Please use 'Season Year'."
    else:
        season, year = season_parts
        season = season.capitalize()
        if season not in possible_seasons:
            error_detail = "Invalid season. Please use 'Winter', 'Spring', 'Summer', or 'Fall'."
        elif not year.isdigit() or len(year) != 4:
            error_detail = "Invalid year. Please use a 4-digit year."
        else:
            query.season = f"{season} {year}"

    if error_detail:
        request_log.record_request(
            endpoint,
            query,
            request,
            http_status=400,
            reason="Invalid season",
            detail=error_detail,
        )

    filters = resolve_song_filters(query, endpoint=endpoint, request=request)
    start = time.perf_counter()
    song_list = get_search_result.get_season_song_list(
        query.season,
        query.ignore_duplicate,
        filters,
    )

    request_log.record_request(
        endpoint,
        query,
        request,
        result_count=len(song_list),
        duration_ms=_elapsed_ms(start),
    )
    return song_list


# Return every possible songartist string for autocompletion
@app.get("/api/artist_autocomplete", response_model=list[str])
async def artist_autocomplete(
    search: str | None = Query(
        None,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Case-insensitive partial match on romaji artist name.",
    ),
    count: int = Query(
        99999, ge=1, description="Maximum number of suggestions to return."
    ),
):
    return sql_calls.autocomplete_artists(search, count)


# Return every possible anime song name string for autocompletion
@app.get("/api/song_name_autocomplete", response_model=list[str])
async def song_name_autocomplete(
    search: str | None = Query(
        None,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Case-insensitive partial match on romaji song name.",
    ),
    count: int = Query(
        99999, ge=1, description="Maximum number of suggestions to return."
    ),
):
    return sql_calls.autocomplete_song_names(search, count)


# Return every possible anime name string for autocompletion with possible filters on song_name and artist
@app.get("/api/anime_name_autocomplete", response_model=list[str])
async def anime_name_autocomplete(
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
    return sql_calls.autocomplete_anime_names(songName, songArtist)


# Return a .json dict containing every key annId value linked_ids
@app.get(
    "/api/annid_linked_ids",
    response_model=dict[int, AnnIdLinkedAnimeEntry],
    response_model_by_alias=False,
)
async def annid_linked_ids():
    return sql_calls.get_annid_linked_ids()


# Return information about ranked restrictions
@app.get("/api/ranked_time_status", response_model=RankedTimeStatus)
async def get_ranked_time_status():
    return utils.get_ranked_time_info()


# Return stats and song counts to monitor the DB
@app.get("/api/database_totals", response_model=DatabaseTotals)
async def get_database_totals():
    totals = sql_calls.get_database_totals()
    return DatabaseTotals(**totals)


# Serve log-viewer.html and request log JSON feed
log_path = request_log.get_request_log_path()
log_viewer = Path(__file__).resolve().parent / "log-viewer.html"

if log_path and log_viewer.is_file():

    @app.get(f"/{log_path}", include_in_schema=False)
    async def request_log_viewer_page():
        return FileResponse(log_viewer, media_type="text/html")

    @app.get(f"/{log_path}/feed", include_in_schema=False)
    async def request_log_feed(since: str | None = None, limit: int = 100):
        return request_log.get_feed_payload(since=since, limit=limit)
