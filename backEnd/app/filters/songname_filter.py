import re
from filters import utils


def song_meets_search_requirement(
    search, song, case_sensitive, authorized_types,
):

    """
    Check that a song meets the settings
    """

    if song["type"] not in authorized_types:
        return False

    if (not case_sensitive and re.match(search, song["song_name"], re.IGNORECASE)) or (
        case_sensitive and re.match(search, song["song_name"])
    ):
        return True

    return False


def search_songName(
    song_database,
    search,
    ignore_special_character=True,
    partial_match=True,
    case_sensitive=False,
    max_nb_songs=250,
    authorized_types=[],
):

    search = utils.get_regex_search(search, ignore_special_character, partial_match)

    song_list = []
    for song in song_database:
        if len(song_list) >= max_nb_songs:
            break
        if song_meets_search_requirement(
            search, song, case_sensitive, authorized_types
        ):
            song_list.append(utils.format_song(song))
    return song_list
