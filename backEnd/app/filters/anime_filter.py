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

    # Check if search match with an anime name
    if (
        song["type"] in authorized_types
        and (
            not case_sensitive
            and (
                re.match(search, song["anime_eng_name"], re.IGNORECASE)
                or (
                    song["anime_jp_name"]
                    and re.match(search, song["anime_jp_name"], re.IGNORECASE)
                )
            )
        )
        or (
            case_sensitive
            and (
                re.match(search, song["anime_eng_name"])
                or (song["anime_jp_name"] and re.match(search, song["anime_jp_name"]))
            )
        )
    ):
        return True

    return False


def search_anime(
    song_database,
    search,
    ignore_special_character=True,
    partial_match=True,
    case_sensitive=False,
    max_nb_songs=250,
    authorized_types=[],
):

    song_list = []

    # If the search is an ANNID
    if str(search).isdecimal():
        for song in song_database:
            if len(song_list) >= max_nb_songs:
                break
            if song["annId"] == int(search) and song["type"] in authorized_types:
                song_list.append(utils.format_song(song))

    # If not
    search = utils.get_regex_search(search, ignore_special_character, partial_match)

    for song in song_database:
        if len(song_list) >= max_nb_songs:
            break

        if song_meets_search_requirement(
            search, song, case_sensitive, authorized_types
        ):
            song_list.append(utils.format_song(song))

    return song_list
