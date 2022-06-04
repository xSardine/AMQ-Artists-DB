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
import timeit
import json
import random
from datetime import datetime


def add_log(log_data):

    with open("../logs.json") as json_file:
        data = json.load(json_file)

    data.append(log_data)

    with open("../logs.json", "w") as outfile:
        json.dump(data, outfile)


def is_duplicate_in_list(list, song):
    for song2 in list:
        if (
            song["songName"] == song2["songName"]
            and song["songArtist"] == song2["songArtist"]
        ):
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


def get_50_random_songs(song_database):

    song_list = []
    for i in range(50):
        song_list.append(utils.format_song(random.choice(song_database)))
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

    logs = {
        "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
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

    for key in logs:
        print(f"{key}: {logs[key]}")

    artist_result_list = []
    anime_result_list = []
    songname_result_list = []
    annId_result_list = []
    composer_result_list = []

    date = datetime.utcnow()
    is_ranked = False
    # If ranked time UTC
    if (
        # CST
        (
            (date.hour == 1 and date.minute <= 30)
            or (date.hour == 2 and date.minute >= 30)
        )
        # JST
        or (
            (date.hour == 11 and date.minute <= 30)
            or (date.hour == 12 and date.minute >= 30)
        )
        # CET
        or (
            (date.hour == 18 and date.minute <= 30)
            or (date.hour == 19 and date.minute >= 30)
        )
    ):
        is_ranked = True

    # if main filter
    if (
        type(anime_search_filters) != list
        and type(song_name_search_filters) != list
        and type(artist_search_filters) != list
        and anime_search_filters.search == song_name_search_filters.search
        and song_name_search_filters.search == artist_search_filters.search
    ):

        if not is_ranked:
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

    if type(artist_search_filters) != list and not is_ranked:
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

    if type(song_name_search_filters) != list and not is_ranked:
        songname_result_list = songname_filter.search_songName(
            song_database,
            song_name_search_filters.search,
            song_name_search_filters.ignore_special_character,
            song_name_search_filters.partial_match,
            song_name_search_filters.case_sensitive,
            max_nb_songs - len(artist_result_list + anime_result_list),
            authorized_types,
        )

    if type(composer_search_filters) != list and not is_ranked:
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
    logs["computing_time"] = round(stop - start, 4)
    logs["nb_results"] = len(song_list)
    add_log(logs)
    print(f"computing_time: {logs['computing_time']}")
    print(f"nb_results: {logs['nb_results']}")
    print()

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

    logs = {
        "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        "artist_ids_filter": artist_ids,
        "ignore_dups": ignore_duplicate,
        "max_nb_songs": max_nb_songs,
        "types": authorized_types,
    }

    for key in logs:
        print(f"{key}: {logs[key]}")

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

    logs["computing_time"] = round(stop - start, 4)
    logs["nb_results"] = len(song_list)
    add_log(logs)
    print(f"computing_time: {logs['computing_time']}")
    print(f"nb_results: {logs['nb_results']}")
    print()

    return song_list


def get_annId_song_list(
    song_database,
    annId,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
):

    start = timeit.default_timer()

    logs = {
        "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        "annId_filter": annId,
        "ignore_dups": ignore_duplicate,
        "max_nb_songs": max_nb_songs,
        "types": authorized_types,
    }

    for key in logs:
        print(f"{key}: {logs[key]}")

    song_list = annId_filter.search_annId(
        song_database,
        annId,
        max_nb_songs,
        authorized_types,
    )

    song_list = combine_results(song_list, [], [], [], [], False, ignore_duplicate)

    stop = timeit.default_timer()

    logs["computing_time"] = round(stop - start, 4)
    logs["nb_results"] = len(song_list)
    add_log(logs)
    print(f"computing_time: {logs['computing_time']}")
    print(f"nb_results: {logs['nb_results']}")
    print()

    return song_list
