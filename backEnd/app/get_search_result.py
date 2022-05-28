from filters import (
    anime_filter,
    artist_filter,
    songname_filter,
    links_filter,
    annId_filter,
    composer_filter,
    utils,
)
from datetime import datetime
from pathlib import Path
import timeit
import json


def add_log(log_data):

    with open("../logs.json") as json_file:
        data = json.load(json_file)

    data.append(log_data)

    for key in log_data:
        print(f"{key}: {log_data[key]}")
    print()

    with open("../logs.json", "w") as outfile:
        json.dump(data, outfile)


def is_duplicate_in_list(list, song):
    for song2 in list:
        if song["SongName"] == song2["SongName"] and song["Artist"] == song2["Artist"]:
            return True
    return False


def combine_results(
    artist_song_list,
    anime_song_list,
    songname_song_list,
    annId_result_list,
    composer_result_list,
    and_logic=False,
    ignore_duplicate=False,
    max_nb_songs=300,
):

    final_song_list = []
    for song in (
        artist_song_list
        + anime_song_list
        + songname_song_list
        + annId_result_list
        + composer_result_list
    ):
        if len(final_song_list) >= max_nb_songs:
            break

        if song in final_song_list:
            continue

        if and_logic:
            if (
                (not artist_song_list or song in artist_song_list)
                and (not anime_song_list or song in anime_song_list)
                and (not songname_song_list or song in songname_song_list)
                and (not composer_result_list or song in composer_result_list)
            ):
                if not ignore_duplicate or not is_duplicate_in_list(
                    final_song_list, song
                ):
                    final_song_list.append(song)
        else:
            if not ignore_duplicate or not is_duplicate_in_list(final_song_list, song):
                final_song_list.append(song)

    return final_song_list


def get_first_n_songs(song_database, nb_songs):

    song_list = []
    for song in song_database:
        if len(song_list) < nb_songs:
            song_list.append(utils.format_song(song))
        else:
            return song_list
    return song_list


def get_search_results(
    song_database,
    artist_database,
    anime_search_filters,
    song_name_search_filters,
    artist_search_filters,
    composer_search_filters,
    and_logic,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
):

    start = timeit.default_timer()

    artist_result_list = []
    anime_result_list = []
    songname_result_list = []
    annId_result_list = []
    composer_result_list = []

    # if main filter
    if (
        type(anime_search_filters) != list
        and type(song_name_search_filters) != list
        and type(artist_search_filters) != list
        and anime_search_filters.search == song_name_search_filters.search
        and song_name_search_filters.search == artist_search_filters.search
    ):

        # search for .webm and .mp3
        link_search = links_filter.search_link(
            song_database, anime_search_filters.search
        )
        if len(link_search) > 0:
            return link_search

        # search for annID

        annId_result_list = annId_filter.search_annId(
            song_database, anime_search_filters.search, max_nb_songs, authorized_types
        )

    if type(anime_search_filters) != list:

        anime_result_list = anime_filter.search_anime(
            song_database,
            anime_search_filters.search,
            anime_search_filters.ignore_special_character,
            anime_search_filters.partial_match,
            anime_search_filters.case_sensitive,
            max_nb_songs,
            authorized_types,
        )

    if type(artist_search_filters) != list:
        artist_result_list = artist_filter.search_artist(
            song_database,
            artist_database,
            artist_search_filters.search,
            artist_search_filters.group_granularity,
            artist_search_filters.max_other_artist,
            artist_search_filters.ignore_special_character,
            artist_search_filters.partial_match,
            artist_search_filters.case_sensitive,
            max_nb_songs - len(anime_result_list),
            authorized_types,
        )

    if type(song_name_search_filters) != list:
        songname_result_list = songname_filter.search_songName(
            song_database,
            song_name_search_filters.search,
            song_name_search_filters.ignore_special_character,
            song_name_search_filters.partial_match,
            song_name_search_filters.case_sensitive,
            max_nb_songs - len(artist_result_list + anime_result_list),
            authorized_types,
        )

    if type(composer_search_filters) != list:
        composer_result_list = composer_filter.search_composer(
            song_database,
            artist_database,
            composer_search_filters.search,
            composer_search_filters.ignore_special_character,
            composer_search_filters.partial_match,
            composer_search_filters.case_sensitive,
            composer_search_filters.arrangement,
            max_nb_songs - len(artist_result_list + anime_result_list),
            authorized_types,
        )

    song_list = combine_results(
        artist_result_list,
        anime_result_list,
        songname_result_list,
        annId_result_list,
        composer_result_list,
        and_logic,
        ignore_duplicate,
        max_nb_songs,
    )

    stop = timeit.default_timer()

    logs = {
        "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        "nb_results": len(song_list),
        "computing_time": round(stop - start, 4),
    }
    if anime_search_filters:
        logs["anime_filter"] = {
            "search": anime_search_filters.search,
            "ignore_special_characters": anime_search_filters.ignore_special_character,
            "partial_match": anime_search_filters.partial_match,
            "case_sensitive": anime_search_filters.case_sensitive,
        }
    if song_name_search_filters:
        logs["song_filter"] = {
            "search": song_name_search_filters.search,
            "ignore_special_characters": song_name_search_filters.ignore_special_character,
            "partial_match": song_name_search_filters.partial_match,
            "case_sensitive": song_name_search_filters.case_sensitive,
        }
    if artist_search_filters:
        logs["artist_filter"] = {
            "search": artist_search_filters.search,
            "ignore_special_characters": artist_search_filters.ignore_special_character,
            "partial_match": artist_search_filters.partial_match,
            "case_sensitive": artist_search_filters.case_sensitive,
            "group_granularity": artist_search_filters.group_granularity,
            "max_other_people": artist_search_filters.max_other_artist,
        }
    if composer_search_filters:
        logs["composer_filter"] = {
            "search": composer_search_filters.search,
            "ignore_special_characters": composer_search_filters.ignore_special_character,
            "partial_match": composer_search_filters.partial_match,
            "case_sensitive": composer_search_filters.case_sensitive,
            "arrangement": composer_search_filters.arrangement,
        }
    logs["is_intersection"] = and_logic
    logs["ignore_dups"] = ignore_duplicate
    logs["max_nb_songs"] = max_nb_songs
    logs["types"] = authorized_types

    add_log(logs)

    return song_list


def get_artists_ids_song_list(
    song_database,
    artist_database,
    artist_ids,
    max_other_artist,
    group_granularity,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
):

    start = timeit.default_timer()

    song_list = artist_filter.search_artist_ids(
        song_database,
        artist_database,
        artist_ids,
        group_granularity,
        max_other_artist,
        max_nb_songs,
        authorized_types,
    )

    song_list = combine_results(song_list, [], [], [], [], False, ignore_duplicate)

    stop = timeit.default_timer()

    log = f"\n{datetime.now().time()}: I have found {len(song_list)} songs for the search {artist_ids}, ignore dups: {ignore_duplicate}, max songs: {max_nb_songs}, types: {authorized_types}\n"
    log += f"Search time: {stop - start}\n"

    add_log(
        {
            "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
            "nb_results": len(song_list),
            "computing_time": round(stop - start, 4),
            "artist_ids_filter": artist_ids,
            "ignore_dups": ignore_duplicate,
            "max_nb_songs": max_nb_songs,
            "types": authorized_types,
        }
    )

    return song_list


def get_annId_song_list(
    song_database,
    annId,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
):

    start = timeit.default_timer()

    song_list = annId_filter.search_annId(
        song_database,
        annId,
        max_nb_songs,
        authorized_types,
    )

    stop = timeit.default_timer()

    song_list = combine_results(song_list, [], [], [], [], False, ignore_duplicate)

    log = f"\n{datetime.now().time()}: I have found {len(song_list)} songs for the search {annId}, ignore dups: {ignore_duplicate}, max songs: {max_nb_songs}, types: {authorized_types}\n"
    log += f"Search time: {stop - start}\n"

    add_log(
        {
            "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
            "nb_results": len(song_list),
            "computing_time": round(stop - start, 4),
            "annId_filter": annId,
            "ignore_dups": ignore_duplicate,
            "max_nb_songs": max_nb_songs,
            "types": authorized_types,
        }
    )

    return song_list
