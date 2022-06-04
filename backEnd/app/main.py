from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import get_search_result
from filters import artist_filter
import sql_calls


class Search_Filter(BaseModel):

    search: str
    ignore_special_character: Optional[bool] = True
    partial_match: Optional[bool] = True
    case_sensitive: Optional[bool] = False

    # How much I decompose the group to search for other songs
    # ie. 1: Artists one by one 2: At least two member from the group, etc...
    group_granularity: Optional[int] = Field(2, ge=0)
    # Once I've confirmed group_granularity requirement is met
    # How much other artists that are not from the og group do I accept
    max_other_artist: Optional[int] = Field(2, ge=0)

    # for composer search
    arrangement: Optional[bool] = False

    class Config:
        schema_extra = {
            "example": {
                "search": "fripSide",
                "ignore_special_character": True,
                "partial_match": True,
                "case_sensitive": False,
                "group_granularity": 1,
                "max_other_artist": 2,
            }
        }

    # This will search for every fripSide song, as well as every Yoshino Nanjo song with not more than 2 other artists


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

    class Config:
        schema_extra = {
            "example": {
                "anime_search_filter": {
                    "search": "White Album",
                    "ignore_special_character": True,
                    "partial_match": True,
                    "case_sensitive": False,
                    "max_artist_per_songs": 99,
                },
                "artist_search_filter": {
                    "search": "Madoka Yonezawa",
                    "ignore_special_character": True,
                    "partial_match": True,
                    "case_sensitive": False,
                    "max_artist_per_songs": 99,
                },
            }
        }


class Artist_ID_Search_Request(BaseModel):

    artist_ids: List[int] = []
    group_granularity: Optional[int] = Field(2, ge=0)
    max_other_artist: Optional[int] = Field(2, ge=0)
    ignore_duplicate: Optional[bool] = False
    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True


class annId_Search_Request(BaseModel):

    annId: int
    ignore_duplicate: Optional[bool] = False
    opening_filter: Optional[bool] = True
    ending_filter: Optional[bool] = True
    insert_filter: Optional[bool] = True


class artist(BaseModel):

    id: int
    names: List[str]
    groups: Optional[List[artist]]
    members: Optional[List[artist]]


artist.update_forward_refs()


class Song_Entry(BaseModel):

    annId: int
    annSongId: int
    animeExpandName: str
    animeENName: Optional[str]
    animeJPName: Optional[str]
    animeVintage: Optional[str]
    animeType: Optional[str]
    songType: str
    songName: str
    songArtist: str
    songDifficulty: Optional[float]
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


def format_artist_ids(artist_database, artist_id):
    artist = {"id": artist_id[0]}

    alt_names = artist_filter.get_artist_names(artist_database, artist_id[0])
    artist["names"] = alt_names

    artist_groups = artist_filter.get_groups_with_artist(artist_database, artist_id[0])
    if len(artist_groups) > 0:
        temp_list = []
        for artist_group in artist_groups:
            temp_list.append(
                {
                    "id": artist_group,
                    "names": artist_filter.get_artist_names(
                        artist_database, artist_group
                    ),
                }
            )
        artist["groups"] = temp_list

    group_members = artist_filter.get_artists_in_group(
        artist_database, artist_id[0], artist_id[1]
    )

    if group_members != None and not (
        len(group_members) == 1 and group_members[0] == artist_id[0]
    ):
        temp_list = []
        for group_member in group_members:
            temp_list.append(
                {
                    "id": group_member,
                    "names": artist_filter.get_artist_names(
                        artist_database, group_member
                    ),
                }
            )
        artist["members"] = temp_list

    return artist


def format_composer_ids(artist_database, composer_id):
    composer = {"id": composer_id}

    alt_names = artist_filter.get_artist_names(artist_database, composer_id)
    composer["names"] = alt_names

    return composer


def format_arranger_ids(artist_database, arranger_id):
    arranger = {"id": arranger_id}

    alt_names = artist_filter.get_artist_names(artist_database, arranger_id)
    arranger["names"] = alt_names

    return arranger


@app.post("/api/search_request", response_model=List[Song_Entry])
async def search_request(query: Search_Request):

    song_database = sql_calls.extract_song_database()
    artist_database = sql_calls.extract_artist_database()

    authorized_type = []
    if query.opening_filter:
        authorized_type.append(1)
    if query.ending_filter:
        authorized_type.append(2)
    if query.insert_filter:
        authorized_type.append(3)

    if not authorized_type:
        return []

    song_list = get_search_result.get_search_results(
        song_database,
        artist_database,
        query.anime_search_filter,
        query.song_name_search_filter,
        query.artist_search_filter,
        query.composer_search_filter,
        query.and_logic,
        query.ignore_duplicate,
        300,
        authorized_type,
    )

    for song in song_list:
        artist_list = []
        for artist_id in song["artists"]:
            artist_list.append(format_artist_ids(artist_database, artist_id))
        song["artists"] = artist_list

        composer_list = []
        for composer_id in song["composers"]:
            composer_list.append(format_composer_ids(artist_database, composer_id))
        song["composers"] = composer_list

        arranger_list = []
        for arranger_id in song["arrangers"]:
            arranger_list.append(format_arranger_ids(artist_database, arranger_id))
        song["arrangers"] = arranger_list

    return song_list


@app.post("/api/get_50_random_songs", response_model=List[Song_Entry])
async def get_50_random_songs():

    song_database = sql_calls.extract_song_database()
    artist_database = sql_calls.extract_artist_database()

    data = get_search_result.get_50_random_songs(song_database)

    for song in data:
        artist_list = []
        for artist_id in song["artists"]:
            artist_list.append(format_artist_ids(artist_database, artist_id))
        song["artists"] = artist_list

        composer_list = []
        for composer_id in song["composers"]:
            composer_list.append(format_composer_ids(artist_database, composer_id))
        song["composers"] = composer_list

        arranger_list = []
        for arranger_id in song["arrangers"]:
            arranger_list.append(format_arranger_ids(artist_database, arranger_id))
        song["arrangers"] = arranger_list

    return data


@app.post("/api/artist_ids_request", response_model=List[Song_Entry])
async def search_request(query: Artist_ID_Search_Request):

    song_database = sql_calls.extract_song_database()
    artist_database = sql_calls.extract_artist_database()

    authorized_type = []
    if query.opening_filter:
        authorized_type.append(1)
    if query.ending_filter:
        authorized_type.append(2)
    if query.insert_filter:
        authorized_type.append(3)

    if not authorized_type:
        return []

    song_list = get_search_result.get_artists_ids_song_list(
        song_database,
        artist_database,
        query.artist_ids,
        query.max_other_artist,
        query.group_granularity,
        query.ignore_duplicate,
        300,
        authorized_type,
    )

    for song in song_list:
        artist_list = []
        for artist_id in song["artists"]:
            artist_list.append(format_artist_ids(artist_database, artist_id))
        song["artists"] = artist_list

        composer_list = []
        for composer_id in song["composers"]:
            composer_list.append(format_composer_ids(artist_database, composer_id))
        song["composers"] = composer_list

        arranger_list = []
        for arranger_id in song["arrangers"]:
            arranger_list.append(format_arranger_ids(artist_database, arranger_id))
        song["arrangers"] = arranger_list

    return song_list


@app.post("/api/annId_request", response_model=List[Song_Entry])
async def search_request(query: annId_Search_Request):

    song_database = sql_calls.extract_song_database()
    artist_database = sql_calls.extract_artist_database()

    authorized_type = []
    if query.opening_filter:
        authorized_type.append(1)
    if query.ending_filter:
        authorized_type.append(2)
    if query.insert_filter:
        authorized_type.append(3)

    if not authorized_type:
        return []

    song_list = get_search_result.get_annId_song_list(
        song_database,
        query.annId,
        query.ignore_duplicate,
        300,
        authorized_type,
    )

    for song in song_list:
        artist_list = []
        for artist_id in song["artists"]:
            artist_list.append(format_artist_ids(artist_database, artist_id))
        song["artists"] = artist_list

        composer_list = []
        for composer_id in song["composers"]:
            composer_list.append(format_composer_ids(artist_database, composer_id))
        song["composers"] = composer_list

        arranger_list = []
        for arranger_id in song["arrangers"]:
            arranger_list.append(format_arranger_ids(artist_database, arranger_id))
        song["arrangers"] = arranger_list

    return song_list
