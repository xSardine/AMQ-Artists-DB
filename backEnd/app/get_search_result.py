from filters import anime_filter
from filters import artist_filter
from filters import songname_filter
from filters import utils
from datetime import datetime


def is_duplicate_in_list(list, song, ignore_duplicate):
    for song2 in list:
        if song["SongName"] == song2["SongName"] and song["Artist"] == song2["Artist"]:
            if ignore_duplicate or song["Anime"] == song2["Anime"]:
                return True
    return False


def is_song_in_list(song_list, song):
    for song2 in song_list:
        if song == song2:
            return True
    return False


def combine_results(
    artist_song_list,
    anime_song_list,
    songname_song_list,
    and_logic=False,
    ignore_duplicate=False,
    max_nb_songs=250,
):

    final_song_list = []
    for song in artist_song_list + anime_song_list + songname_song_list:
        if len(final_song_list) >= max_nb_songs:
            break
        if and_logic:
            if (
                (is_song_in_list(artist_song_list, song) or len(artist_song_list) == 0)
                and (
                    is_song_in_list(anime_song_list, song) or len(anime_song_list) == 0
                )
                and (
                    is_song_in_list(songname_song_list, song)
                    or len(songname_song_list) == 0
                )
            ):
                if not is_duplicate_in_list(final_song_list, song, ignore_duplicate):
                    final_song_list.append(song)

        else:
            if not is_duplicate_in_list(final_song_list, song, ignore_duplicate):
                final_song_list.append(song)

    return final_song_list


def get_first_n_songs(song_database, nb_songs):

    count = 0
    song_list = []
    for anime in song_database:
        for song in anime["songs"]:
            if count < nb_songs:
                song_list.append(utils.format_song(anime["annId"], anime["name"], song))
                count += 1
            else:
                return song_list
    return song_list


def get_search_results(
    song_database,
    artist_database,
    group_database,
    anime_search_filters,
    song_name_search_filters,
    artist_search_filters,
    and_logic,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
):

    artist_result_list = []
    anime_result_list = []
    songname_result_list = []

    if type(artist_search_filters) != list:
        artist_result_list = artist_filter.search_artist(
            song_database,
            artist_database,
            group_database,
            artist_search_filters.search,
            artist_search_filters.group_granularity,
            artist_search_filters.max_other_artist,
            artist_search_filters.ignore_special_character,
            artist_search_filters.partial_match,
            artist_search_filters.case_sensitive,
            max_nb_songs,
            authorized_types,
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

    if type(song_name_search_filters) != list:
        songname_result_list = songname_filter.search_songName(
            song_database,
            song_name_search_filters.search,
            song_name_search_filters.ignore_special_character,
            song_name_search_filters.partial_match,
            song_name_search_filters.case_sensitive,
            max_nb_songs,
            authorized_types,
        )

    song_list = combine_results(
        artist_result_list,
        anime_result_list,
        songname_result_list,
        and_logic,
        ignore_duplicate,
        max_nb_songs,
    )

    print(
        datetime.now().time(),
        ": I have found",
        len(song_list),
        "songs for the search",
        anime_search_filters,
        song_name_search_filters,
        artist_search_filters,
        "and_logic:",
        and_logic,
        "ignore dups:",
        ignore_duplicate,
        "max songs:",
        max_nb_songs,
        "types:",
        authorized_types,
    )

    return song_list
