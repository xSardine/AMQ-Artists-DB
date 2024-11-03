from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import get_search_result
import sql_calls, utils
from random import randrange


class Search_Filter(BaseModel):
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
        schema_extra = {
            "example": {
                "search": "fripSide",
                "partial_match": True,
                "group_granularity": 1,
                "max_other_artist": 2,
            }
        }


class Search_Request(BaseModel):
    anime_search_filter: Optional[Search_Filter] = []
    song_name_search_filter: Optional[Search_Filter] = []
    artist_search_filter: Optional[Search_Filter] = []
    composer_search_filter: Optional[Search_Filter] = []

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
        schema_extra = {
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


class Artist_ID_Search_Request(BaseModel):
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


class Composer_ID_Search_Request(BaseModel):
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


class annId_Search_Request(BaseModel):
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


class malIds_Search_Request(BaseModel):
    malIds: List[int] = []
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


class artist(BaseModel):
    id: int
    names: List[str]
    line_up_id: Optional[int]
    groups: Optional[List[artist]]
    members: Optional[List[artist]]


artist.update_forward_refs()


class Anime_List_Links(BaseModel):
    myanimelist: Optional[int]
    anidb: Optional[int]
    anilist: Optional[int]
    kitsu: Optional[int]


class Song_Entry(BaseModel):
    annId: int
    annSongId: int
    animeENName: str
    animeJPName: str
    animeAltName: Optional[List[str]]
    animeVintage: Optional[str]
    linked_ids: Anime_List_Links
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
    artists: List[artist]
    composers: List[artist]
    arrangers: List[artist]


# Launch API
app = FastAPI()

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


@app.post("/api/search_request", response_model=List[Song_Entry])
async def search_request(query: Search_Request):
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
        return []

    if not authorized_broadcasts:
        return []

    if not authorized_song_categories:
        return []

    song_list = get_search_result.get_search_results(
        query.anime_search_filter,
        query.song_name_search_filter,
        query.artist_search_filter,
        query.composer_search_filter,
        query.and_logic,
        query.ignore_duplicate,
        300,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/get_50_random_songs", response_model=List[Song_Entry])
async def get_50_random_songs():
    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    songIds = [randrange(28000) for i in range(50)]

    artist_database = sql_calls.extract_artist_database()

    # Extract every song from song IDs
    get_songs_from_songs_ids = (
        f"SELECT * from songsFull WHERE songId IN ({','.join('?'*len(songIds))})"
    )
    songs = sql_calls.run_sql_command(cursor, get_songs_from_songs_ids, songIds)

    song_list = [utils.format_song(artist_database, song) for song in songs]

    return song_list


@app.post("/api/artist_ids_request", response_model=List[Song_Entry])
async def search_request(query: Artist_ID_Search_Request):

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
        return []

    if not authorized_broadcasts:
        return []

    if not authorized_song_categories:
        return []

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


@app.post("/api/composer_ids_request", response_model=List[Song_Entry])
async def search_request(query: Composer_ID_Search_Request):

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

    song_list = get_search_result.get_composer_ids_song_list(
        query.composer_ids,
        query.arrangement,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/annId_request", response_model=List[Song_Entry])
async def search_request(query: annId_Search_Request):

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
        return []

    if not authorized_broadcasts:
        return []

    if not authorized_song_categories:
        return []

    song_list = get_search_result.get_annId_song_list(
        query.annId,
        query.ignore_duplicate,
        authorized_type,
        authorized_broadcasts,
        authorized_song_categories,
    )

    return song_list


@app.post("/api/malIDs_request")
async def malIDs_request(query: malIds_Search_Request):

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
        return []

    if not authorized_broadcasts:
        return []

    if not authorized_song_categories:
        return []

    if len(query.malIds) > 500:
        # return error message
        return "Too many malIds"

    song_list = get_search_result.get_malIds_song_list(
        query.malIds,
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

    # sort by legnth
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


# api points that returns all songs from a specific season
@app.get("/api/filter_season")
async def filter_season(season: str):

    # check it's correctly formatted
    possible_seasons = ["Winter", "Spring", "Summer", "Fall"]

    if len(season.split(" ")) != 2:
        return f"{season} is an invalid season, please use the format 'Season Year'. Example : 'Winter 2021'"

    sson, year = season.split(" ")
    if sson not in possible_seasons:
        return f"{sson} is an invalid season, please use the format 'Season Year'. Example : 'Winter 2021'"

    if not year.isdigit():
        return f"{year} is an invalid year, please use the format 'Season Year'. Example : 'Winter 2021'"

    if len(year) != 4:
        return f"{year} is an invalid year, please use the format 'Season Year'. Example : 'Winter 2021'"

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    get_all_songs = "SELECT * from songsFull WHERE animeVintage LIKE ?"
    songs = sql_calls.run_sql_command(cursor, get_all_songs, [f"%{season}%"])

    artist_database = sql_calls.extract_artist_database()

    song_list = [utils.format_song(artist_database, song) for song in songs]

    return song_list
