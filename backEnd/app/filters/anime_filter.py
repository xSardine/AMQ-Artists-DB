import re
from filters import utils


def song_meets_search_requirement(
    search,
    song,
    case_sensitive,
    authorized_types,
):

    """
    Check that a song meets the settings
    """

    if song["songType"] not in authorized_types:
        return False

    # Check if search match with an anime name
    if (
        song["songType"] in authorized_types
        and (
            not case_sensitive
            and (
                re.match(search, song["nameExpand"], re.IGNORECASE)
                or (song["nameJP"] and re.match(search, song["nameJP"], re.IGNORECASE))
                or (song["nameEN"] and re.match(search, song["nameEN"], re.IGNORECASE))
            )
        )
        or (
            case_sensitive
            and (
                re.match(search, song["nameExpand"])
                or (song["nameJP"] and re.match(search, song["nameJP"]))
                or (song["nameEN"] and re.match(search, song["nameEN"]))
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
    max_nb_songs=300,
    authorized_types=[],
):

    song_list = []

    search = utils.get_regex_search(search, ignore_special_character, partial_match)

    for song in song_database:
        if len(song_list) >= max_nb_songs:
            break

        if song_meets_search_requirement(
            search, song, case_sensitive, authorized_types
        ):
            song_list.append(utils.format_song(song))

    return song_list
