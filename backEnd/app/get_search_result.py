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


def add_log(log):
    """Append given text as a new line at the end of file"""
    # Open the file in append & read mode ('a+')
    with open("../logs.txt", "a+") as file_object:
        # Move read cursor to the start of file.
        file_object.seek(0)
        # If file is not empty then append '\n'
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\n")
        # Append text at the end of file
        file_object.write(log)


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

    log = f"\n{datetime.now().time()}: I have found {len(song_list)} songs for the search:\n"

    if anime_search_filters:
        log += f"Anime: {anime_search_filters}\n"
    if song_name_search_filters:
        log += f"Song name: {song_name_search_filters}\n"
    if artist_search_filters:
        log += f"Artist: {artist_search_filters}\n"
    if composer_search_filters:
        log += f"Composer: {composer_search_filters}\n"
    log += f"and_logic: {and_logic}, ignore dups: {ignore_duplicate}, max songs: {max_nb_songs}, types: {authorized_types}\n"
    log += f"Search time: {stop - start}\n"

    add_log(log)

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

    add_log(log)

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

    add_log(log)

    return song_list
