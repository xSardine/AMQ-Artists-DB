from __future__ import annotations
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import get_search_result
import sql_calls, utils
from random import randrange


class SearchFilter(BaseModel):
    search: str
    partial_match: Optional[bool] = True

    # How much I decompose the group to search for other songs
    # ie. 1: Artists one by one 2: At least two member from the group, etc...
    group_granularity: Optional[int] = Field(0, ge=0)
    # Once I've confirmed group_granularity requirement is met
    # How much other artists that are not from the og group do I accept
    max_other_artist: Optional[int] = Field(99, ge=0)

    # for composer search
    arrangement: Optional[bool] = True

    class Config:
        # This will search for every fripSide song, as well as every Yoshino Nanjo song with not more than 2 other artists
        json_schema_extra = {
            "example": {
                "search": "fripSide",
                "partial_match": True,
                "group_granularity": 1,
                "max_other_artist": 2,
            }
        }


class SearchRequest(BaseModel):
    anime_search_filter: Optional[SearchFilter] = []
    song_name_search_filter: Optional[SearchFilter] = []
    artist_search_filter: Optional[SearchFilter] = []
    composer_search_filter: Optional[SearchFilter] = []

    and_logic: Optional[bool] = True

    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True

    class Config:
        json_schema_extra = {
            "example": {
                "anime_search_filter": {
                    "search": "White Album",
                    "ignore_special_character": True,
                    "partial_match": True,
                    "max_artist_per_songs": 99,
                },
                "artist_search_filter": {
                    "search": "Madoka Yonezawa",
                    "ignore_special_character": True,
                    "partial_match": True,
                    "max_artist_per_songs": 99,
                },
            }
        }


class ArtistIdSearchRequest(BaseModel):
    artist_ids: List[int] = []
    group_granularity: Optional[int] = Field(99, ge=0)
    max_other_artist: Optional[int] = Field(0, ge=0)
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class ComposerIdSearchRequest(BaseModel):
    composer_ids: List[int] = []
    arrangement: Optional[bool] = True
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class AnnIdSearchRequest(BaseModel):
    annId: int
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class AnnIdsSearchRequest(BaseModel):
    ann_ids: List[int] = []
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class MalIdsSearchRequest(BaseModel):
    mal_ids: List[int] = []
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class AnnSongIdsSearchRequest(BaseModel):
    ann_song_ids: List[int] = []
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class AmqSongIdsSearchRequest(BaseModel):
    amq_song_ids: List[int] = []
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class SeasonSearchRequest(BaseModel):
    season: str
    ignore_duplicate: Optional[bool] = False

    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True

    normal_broadcast: Optional[bool] = True
    dub: Optional[bool] = True
    rebroadcast: Optional[bool] = True

    standard: Optional[bool] = True
    instrumental: Optional[bool] = True
    chanting: Optional[bool] = True
    character: Optional[bool] = True


class Artist(BaseModel):
    id: int
    names: List[str]
    line_up_id: Optional[int] = -1
    groups: Optional[List[Artist]] = None
    members: Optional[List[Artist]] = None


Artist.model_rebuild()


class AnimeListLinks(BaseModel):
    myanimelist: Optional[int]
    anidb: Optional[int]
    anilist: Optional[int]
    kitsu: Optional[int]


class SongEntry(BaseModel):
    annId: int
    annSongId: int
    amqSongId: int
    animeENName: str
    animeJPName: str
    animeAltName: Optional[List[str]]
    animeVintage: Optional[str]
    linked_ids: AnimeListLinks
    animeType: Optional[str]
    animeCategory: Optional[str]
    songType: str
    songName: str
    songArtist: str
    songComposer: str
    songArranger: str
    songDifficulty: Optional[float]
    songCategory: Optional[str]
    songLength: Optional[float]
    isDub: Optional[bool]
    isRebroadcast: Optional[bool]
    HQ: Optional[str]
    MQ: Optional[str]
    audio: Optional[str]
    artists: List[Artist]
    composers: List[Artist]
    arrangers: List[Artist]


# Launch API
app = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1000 bytes

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def format_artist_ids(artist_database, artist_id, artist_line_up=-1):
    artist = artist_database[str(artist_id)]

    formatted_artist = {
        "id": artist_id,
        "names": artist["names"],
    }

    if artist_line_up != -1:
        formatted_artist["line_up_id"] = artist_line_up

    if artist["groups"]:
        formatted_group_list = []
        for group_id, group_line_up_id in artist["groups"]:
            current_group = {
                "id": group_id,
                "names": artist_database[str(group_id)]["names"],
            }
            if group_line_up_id != -1:
                current_group["line_up_id"] = group_line_up_id
            formatted_group_list.append(current_group)
        formatted_artist["groups"] = formatted_group_list

    if artist_line_up != -1 and artist["members"]:
        formatted_member_list = []
        for member_id, member_line_up_id in artist["members"][artist_line_up]:
            current_member = {
                "id": member_id,
                "names": artist_database[str(member_id)]["names"],
            }
            if member_line_up_id:
                current_member["line_up_id"] = member_line_up_id
            formatted_member_list.append(current_member)
        formatted_artist["members"] = formatted_member_list

    return formatted_artist


def format_composer_ids(artist_database, composer_id):
    composer = {"id": composer_id}

    composer["names"] = artist_database[str(composer_id)]["names"]

    return composer


def format_arranger_ids(artist_database, arranger_id):
    arranger = {"id": arranger_id}
    arranger["names"] = artist_database[str(arranger_id)]["names"]

    return arranger

# Process filter parameters from a search request and return authorized lists
# Raises HTTPException if no filters are selected
def process_filters(query):
    authorized_type = []
    if query.opening_filter:
        authorized_type.append(1)
    if query.ending_filter:
        authorized_type.append(2)
    if query.insert_filter:
        authorized_type.append(3)

    authorized_broadcasts = []
    if query.normal_broadcast:
        authorized_broadcasts.append("Normal")
    if query.dub:
        authorized_broadcasts.append("Dub")
    if query.rebroadcast:
        authorized_broadcasts.append("Rebroadcast")

    authorized_song_categories = []
    if query.standard:
        authorized_song_categories.append("Standard")
        authorized_song_categories.append("No Category")
    if query.instrumental:
        authorized_song_categories.append("Instrumental")
    if query.chanting:
        authorized_song_categories.append("Chanting")
    if query.character:
        authorized_song_categories.append("Character")

    if not authorized_type:
        raise HTTPException(
            status_code=400,
            detail="At least one song type filter (opening, ending, or insert) must be enabled."
        )

    if not authorized_broadcasts:
        raise HTTPException(
            status_code=400,
            detail="At least one broadcast type filter (normal, dub, or rebroadcast) must be enabled."
        )

    if not authorized_song_categories:
        raise HTTPException(
            status_code=400,
            detail="At least one song category filter (standard, instrumental, chanting, or character) must be enabled."
        )

    return authorized_type, authorized_broadcasts, authorized_song_categories


@app.post("/api/search_request", response_model=List[SongEntry])
async def search_request(query: SearchRequest):
    # Check if ranked time restrictions apply
    if get_search_result.is_ranked_time():
        # Check if any restricted filters are being used
        if (query.song_name_search_filter and query.song_name_search_filter.search) or \
           (query.artist_search_filter and query.artist_search_filter.search) or \
           (query.composer_search_filter and query.composer_search_filter.search):
            raise HTTPException(
                status_code=503,
                detail="Search temporarily unavailable during ranked time. Song name, artist, and composer searches are disabled."
            )

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    song_list = get_search_result.get_search_results(
        query.anime_search_filter,
        query.song_name_search_filter,
        query.artist_search_filter,
        query.composer_search_filter,
        query.and_logic,
        query.ignore_duplicate,
        500,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/get_50_random_songs", response_model=List[SongEntry])
async def get_50_random_songs():
    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    query = "SELECT * FROM songsFull ORDER BY RANDOM() LIMIT 50"
    cursor.execute(query)
    songs = cursor.fetchall()

    artist_database = sql_calls.extract_artist_database()

    song_list = [utils.format_song(artist_database, song) for song in songs]

    return song_list


@app.post("/api/artist_ids_request", response_model=List[SongEntry])
async def artist_ids_request(query: ArtistIdSearchRequest):
    # Check if ranked time restrictions apply
    if get_search_result.is_ranked_time():
        raise HTTPException(
            status_code=503,
            detail="Artist ID search temporarily unavailable during ranked time."
        )

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    song_list = get_search_result.get_artists_ids_song_list(
        query.artist_ids,
        query.max_other_artist,
        query.group_granularity,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/composer_ids_request", response_model=List[SongEntry])
async def composer_ids_request(query: ComposerIdSearchRequest):
    # Check if ranked time restrictions apply
    if get_search_result.is_ranked_time():
        raise HTTPException(
            status_code=503,
            detail="Composer ID search temporarily unavailable during ranked time."
        )

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    song_list = get_search_result.get_composer_ids_song_list(
        query.composer_ids,
        query.arrangement,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/annId_request", response_model=List[SongEntry], deprecated=True)
async def annId_request(query: AnnIdSearchRequest):

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    song_list = get_search_result.get_ann_ids_song_list(
        [query.annId],
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/ann_ids_request", response_model=List[SongEntry])
async def ann_ids_request(query: AnnIdsSearchRequest):

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    if len(query.ann_ids) > 500:
        raise HTTPException(
            status_code=400, detail="Too many ANN IDs. Maximum allowed is 500."
        )

    song_list = get_search_result.get_ann_ids_song_list(
        query.ann_ids,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/mal_ids_request", response_model=List[SongEntry])
async def mal_ids_request(query: MalIdsSearchRequest):

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    if len(query.mal_ids) > 500:
        raise HTTPException(
            status_code=400, detail="Too many MAL IDs. Maximum allowed is 500."
        )

    song_list = get_search_result.get_mal_ids_song_list(
        query.mal_ids,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/ann_song_ids_request", response_model=List[SongEntry])
async def ann_song_ids_request(query: AnnSongIdsSearchRequest):

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    if len(query.ann_song_ids) > 500:
        raise HTTPException(
            status_code=400, detail="Too many ANN Song IDs. Maximum allowed is 500."
        )

    song_list = get_search_result.get_ann_song_ids_song_list(
        query.ann_song_ids,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/amq_song_ids_request", response_model=List[SongEntry])
async def amq_song_ids_request(query: AmqSongIdsSearchRequest):

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    if len(query.amq_song_ids) > 500:
        raise HTTPException(
            status_code=400, detail="Too many AMQ Song IDs. Maximum allowed is 500."
        )

    song_list = get_search_result.get_amq_song_ids_song_list(
        query.amq_song_ids,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list

# api points that returns all songs from a specific season
@app.post("/api/season_request", response_model=List[SongEntry])
async def season_request(query: SeasonSearchRequest):
    # Validate season format
    possible_seasons = ["Winter", "Spring", "Summer", "Fall"]
    query.season = query.season.capitalize()

    if len(query.season.split(" ")) != 2:
        raise HTTPException(
            status_code=400, detail="Invalid season format. Please use 'Season Year'."
        )

    season, year = query.season.split(" ")
    if season not in possible_seasons:
        raise HTTPException(
            status_code=400, detail="Invalid season. Please use 'Winter', 'Spring', 'Summer', or 'Fall'."
        )

    if not year.isdigit() or len(year) != 4:
        raise HTTPException(
            status_code=400, detail="Invalid year. Please use a 4-digit year."
        )

    authorized_type, authorized_broadcasts, authorized_song_categories = process_filters(query)

    song_list = get_search_result.get_season_song_list(
        query.season,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


# api point that returns every possible songartist string for autocompletion
@app.get("/api/artist_autocomplete")
async def artist_autocomplete(
    search: Optional[str] = None,
    count: Optional[int] = 99999,
):
    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    # search is not case sensitive and can be partial
    if search:
        get_all_artists = (
            "SELECT DISTINCT romajiSongArtist from songs WHERE romajiSongArtist LIKE ?"
        )
        artists = sql_calls.run_sql_command(cursor, get_all_artists, [f"%{search}%"])
    else:
        get_all_artists = "SELECT DISTINCT romajiSongArtist from songs"
        artists = sql_calls.run_sql_command(cursor, get_all_artists, None)

    artist_list = []
    for artist in artists:
        artist = artist[0]
        artist_list.append(artist)

    # sort by value
    artist_list = sorted(artist_list, key=lambda x: x.lower())[0:count]

    return artist_list


# api point that returns every possible anime song name string for autocompletion
@app.get("/api/song_name_autocomplete")
async def song_name_autocomplete(
    search: Optional[str] = None,
    count: Optional[int] = 99999,
):
    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    # search is not case sensitive and can be partial

    if search:
        get_all_song_names = (
            "SELECT DISTINCT romajiSongName from songs WHERE romajiSongName LIKE ?"
        )
        song_names = sql_calls.run_sql_command(
            cursor, get_all_song_names, [f"%{search}%"]
        )
    else:
        get_all_song_names = "SELECT DISTINCT romajiSongName from songs"
        song_names = sql_calls.run_sql_command(cursor, get_all_song_names, None)

    song_name_list = []
    for song_name in song_names:
        song_name = song_name[0]
        song_name_list.append(song_name)

    # sort by length
    song_name_list = sorted(song_name_list, key=lambda x: len(x))[0:count]

    return song_name_list


# api point that returns every possible anime name string for autocompletion
# with possible filters on song_name and artist
@app.get("/api/anime_name_autocomplete")
async def anime_name_autocomplete(
    songName: Optional[str] = None, songArtist: Optional[str] = None
):
    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    if songName and songArtist:
        get_all_anime_names = "SELECT DISTINCT animeJPName, animeENName from songsAnimes WHERE romajiSongName = ? AND romajiSongArtist = ?"
        anime_names = sql_calls.run_sql_command(
            cursor, get_all_anime_names, [songName, songArtist]
        )
    elif songName:
        get_all_anime_names = "SELECT DISTINCT animeJPName, animeENName from songsAnimes WHERE romajiSongName = ?"
        anime_names = sql_calls.run_sql_command(cursor, get_all_anime_names, [songName])
    elif songArtist:
        get_all_anime_names = "SELECT DISTINCT animeJPName, animeENName from songsAnimes WHERE romajiSongArtist = ?"
        anime_names = sql_calls.run_sql_command(
            cursor, get_all_anime_names, [songArtist]
        )
    else:
        get_all_anime_names = (
            "SELECT DISTINCT animeJPName, animeENName from songsAnimes"
        )
        anime_names = sql_calls.run_sql_command(cursor, get_all_anime_names)

    anime_name_list = []
    for anime_name in anime_names:
        anime_name = anime_name[0] or anime_name[1]
        anime_name_list.append(anime_name)

    # sort by value
    anime_name_list = sorted(anime_name_list, key=lambda x: x.lower())

    return anime_name_list


# this endpoint returns a .json dict containing every key annId value linked_ids
@app.get("/api/annid_linked_ids", response_model=dict)
async def annid_linked_ids():
    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    # Optimized single query using JOIN instead of nested loops
    get_all_animes_with_alt_names = """
    SELECT 
        a.annId, a.malId, a.anidbId, a.anilistId, a.kitsuId, a.animeENName, a.animeJPName,
        GROUP_CONCAT(alt.romaji_name, '\\$') as alt_names
    FROM animes a
    LEFT JOIN link_anime_alt_name alt ON a.annId = alt.annId
    GROUP BY a.annId
    """
    
    animes = sql_calls.run_sql_command(cursor, get_all_animes_with_alt_names)

    output_json = {}
    for anime in animes:
        annId, malId, anidbId, anilistId, kitsuId, animeENName, animeJPName, alt_names_concat = anime

        # Parse the concatenated alt names (split by \$ separator)
        alt_names_list = alt_names_concat.split("\\$") if alt_names_concat else []

        output_json[annId] = {
            "animeENName": animeENName,
            "animeJPName": animeJPName,
            "animeAltName": alt_names_list,
            "linked_ids": {
                "annId": annId,
                "myanimelist": malId,
                "anidb": anidbId,
                "anilist": anilistId,
                "kitsu": kitsuId,
            },
        }

    return output_json


# api endpoint that returns information about ranked restrictions
@app.get("/api/ranked_time_status", response_model=dict)
async def get_ranked_time_status():
    # {active: bool, region: Western|Central|Eastern|None, remaining_minutes: int|None, remaining_seconds: int|None, server_time: str}
    return get_search_result.get_ranked_time_info()


# api endpoint that counts the total number of songs, anime, artists, and seasons in the database
@app.get("/api/database_totals", response_model=dict)
async def get_database_totals():
    cursor = sql_calls.connect_to_database(sql_calls.database_path)
    
    # Single optimized query - one table scan approach
    stats_query = """
    SELECT 
        COUNT(*) as total_songs,
        COUNT(DISTINCT annId) as total_anime,
        SUM(songType = 1) as opening_count,
        SUM(songType = 2) as ending_count,
        SUM(songType = 3) as insert_count,
        SUM(isDub = 1) as dub_count,
        SUM(isRebroadcast = 1) as rebroadcast_count,
        SUM(isDub = 0 AND isRebroadcast = 0) as normal_count,
        SUM(HQ IS NOT NULL) as hq_count,
        SUM(MQ IS NOT NULL) as mq_count,
        SUM(audio IS NOT NULL) as audio_count
    FROM songs
    """
    results = sql_calls.run_sql_command(cursor, stats_query)

    # Get main statistics from first row
    first_row = results[0]
    total_songs = first_row[0]
    total_anime = first_row[1]
    
    songs_by_type = {
        "Opening": first_row[2],
        "Ending": first_row[3],
        "Insert": first_row[4]
    }
    
    songs_by_broadcast = {
        "Dub": first_row[5],
        "Rebroadcast": first_row[6],
        "Normal": first_row[7]
    }
    
    links_by_type = {
        "HQ": first_row[8],
        "MQ": first_row[9],
        "audio": first_row[10]
    }

    # Get artist count - separate query because the artists table is independent from the songs table
    artist_count_query = "SELECT COUNT(*) FROM artists"
    artist_results = sql_calls.run_sql_command(cursor, artist_count_query)
    total_artists = artist_results[0][0]
    
    # Get category statistics - separate query because it requires GROUP BY
    # Main query returns 1 row with totals, but categories need multiple rows (one per category)
    category_query = """
    SELECT songCategory, COUNT(*) as count 
    FROM songs 
    WHERE songCategory IS NOT NULL
    GROUP BY songCategory
    """
    category_results = sql_calls.run_sql_command(cursor, category_query)
    songs_by_category = {}
    for row in category_results:
        songs_by_category[row[0]] = row[1]
    
    # Get anime type and season statistics - combined query using songsFull view
    # Both require GROUP BY operations and use the same view
    anime_type_and_season_query = """
    SELECT 
        'anime_type' as data_type,
        animeType as value,
        COUNT(*) as count 
    FROM songsFull 
    WHERE animeType IS NOT NULL
    GROUP BY animeType
    
    UNION ALL
    
    SELECT 
        'season_count' as data_type,
        'total' as value,
        COUNT(DISTINCT animeVintage) as count 
    FROM songsFull 
    WHERE animeVintage IS NOT NULL
    """
    anime_type_and_season_results = sql_calls.run_sql_command(cursor, anime_type_and_season_query)
    
    songs_by_anime_type = {}
    total_seasons = 0
    
    for row in anime_type_and_season_results:
        data_type, value, count = row
        if data_type == "anime_type":
            songs_by_anime_type[value] = count
        elif data_type == "season_count":
            total_seasons = count
        
    
    return {
        "total_songs": total_songs,
        "total_anime": total_anime,
        "total_artists": total_artists,
        "total_seasons": total_seasons,
        "links_by_type": links_by_type,
        "songs_by_type": songs_by_type,
        "songs_by_broadcast": songs_by_broadcast,
        "songs_by_category": songs_by_category,
        "songs_by_anime_type": songs_by_anime_type,
    }
