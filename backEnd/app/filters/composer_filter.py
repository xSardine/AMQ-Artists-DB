import re
from filters import utils


def get_composer_id(
    artist_database, composer, ignore_special_character, partial_match, case_sensitive
):

    """
    Return every composers id corresponding to the filters
    """

    reversed_composer = ""

    if len(re.split(" ", composer)) == 2:
        reversed_composer = " ".join(reversed(re.split(" ", composer)))
        reversed_composer = utils.get_regex_search(
            reversed_composer, ignore_special_character, partial_match
        )

    composer = utils.get_regex_search(composer, ignore_special_character, partial_match)

    id_list = set()

    for composer_id in artist_database:
        if not artist_database[composer_id]["composer"]:
            continue
        for composer_alt_name in get_composer_names(artist_database, composer_id):
            if (
                not case_sensitive
                and (
                    re.match(composer, composer_alt_name, re.IGNORECASE)
                    or (
                        reversed_composer
                        and (
                            re.match(
                                reversed_composer, composer_alt_name, re.IGNORECASE
                            )
                        )
                    )
                )
            ) or (
                case_sensitive
                and (
                    re.match(composer, composer_alt_name)
                    or (
                        reversed_composer
                        and re.match(reversed_composer, composer_alt_name)
                    )
                )
            ):
                id_list.add(composer_id)
    return id_list


def get_composer_names(artist_database, composer_id):

    """
    Return the list of names corresponding to an composer
    """

    if str(composer_id) not in artist_database:
        return []

    alt_names = [artist_database[str(composer_id)]["name"]]
    if artist_database[str(composer_id)]["alt_names"]:
        for alt_name in artist_database[str(composer_id)]["alt_names"]:
            alt_names.append(alt_name)
    return alt_names


def song_meets_composer_search_requirements(
    song,
    composer_id_list,
    arrangement,
    authorized_types,
):

    if song["songType"] not in authorized_types:
        return False

    for composer in composer_id_list:

        if int(composer) in song["composers_ids"]:
            return True

        if not arrangement:
            continue
        if int(composer) in song["arrangers_ids"]:
            return True

    return False


def search_composer(
    song_database,
    artist_database,
    search,
    ignore_special_character=True,
    partial_match=True,
    case_sensitive=False,
    arrangement=False,
    max_nb_songs=300,
    authorized_types=[],
):

    """
    Return a list of songs corresponding to the search
    """

    composer_id_list = get_composer_id(
        artist_database, search, ignore_special_character, partial_match, case_sensitive
    )

    song_list = []

    if not composer_id_list:
        return []

    for song in song_database:

        if len(song_list) >= max_nb_songs:
            break

        if song_meets_composer_search_requirements(
            song,
            composer_id_list,
            arrangement,
            authorized_types,
        ):
            song_list.append(utils.format_song(song))

    return song_list
