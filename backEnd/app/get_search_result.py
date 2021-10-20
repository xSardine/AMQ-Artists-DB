from filters import anime_filter
from filters import artist_filter
from filters import songname_filter
from filters import links_filter
from filters import utils
from datetime import datetime


def is_duplicate_in_list(list, song):
    for song2 in list:
        if song["SongName"] == song2["SongName"] and song["Artist"] == song2["Artist"]:
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
                (not artist_song_list or song in artist_song_list)
                and (not anime_song_list or song in anime_song_list)
                and (not songname_song_list or song in songname_song_list)
            ):
                if not ignore_duplicate or not is_duplicate_in_list(
                    final_song_list, song
                ):
                    final_song_list.append(song)
        else:
            if song not in final_song_list and (
                not ignore_duplicate or not is_duplicate_in_list(final_song_list, song)
            ):
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
    and_logic,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
):

    artist_result_list = []
    anime_result_list = []
    songname_result_list = []

    if type(artist_search_filters) != list:
        link_search = links_filter.search_link(
            song_database, artist_search_filters.search
        )
        if len(link_search) > 0:
            return link_search
        artist_result_list = artist_filter.search_artist(
            song_database,
            artist_database,
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
            max_nb_songs - len(artist_result_list),
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

    song_list = combine_results(
        artist_result_list,
        anime_result_list,
        songname_result_list,
        and_logic,
        ignore_duplicate,
        max_nb_songs,
    )

    recap_string = f"\n{datetime.now().time()}: I have found {len(song_list)} songs for the search:\n"

    if anime_search_filters:
        recap_string += f"Anime: {anime_search_filters}\n"
    if song_name_search_filters:
        recap_string += f"Song name: {song_name_search_filters}\n"
    if artist_search_filters:
        recap_string += f"Artist: {artist_search_filters}\n"
    recap_string += f"and_logic: {and_logic}, ignore dups: {ignore_duplicate}, max songs: {max_nb_songs}, types: {authorized_types}\n"

    print(recap_string)

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

    song_list = artist_filter.search_artist_ids(
        song_database,
        artist_database,
        artist_ids,
        group_granularity,
        max_other_artist,
        max_nb_songs,
        authorized_types,
    )

    song_list = combine_results(song_list, [], [], False, ignore_duplicate)

    print(
        "\n",
        datetime.now().time(),
        ": I have found",
        len(song_list),
        "songs for the search",
        artist_ids,
        "ignore dups:",
        ignore_duplicate,
        "max songs:",
        max_nb_songs,
        "types:",
        authorized_types,
        "\n",
    )

    return song_list
