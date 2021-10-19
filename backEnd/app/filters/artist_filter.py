import re
from filters import utils


def get_artist_id(
    artist_database, artist, ignore_special_character, partial_match, case_sensitive
):

    """
    Return every artists id corresponding to the filters
    """

    reversed_artist = ""

    if len(re.split(" ", artist)) == 2:
        reversed_artist = " ".join(reversed(re.split(" ", artist)))

    artist = utils.get_regex_search(artist, ignore_special_character, partial_match)

    if reversed_artist:
        reversed_artist = utils.get_regex_search(
            reversed_artist, ignore_special_character, partial_match
        )

    id_list = []

    for id in artist_database.keys():
        for artist_alt_name in artist_database[id]["names"]:
            if (
                case_sensitive
                and (
                    re.match(artist, artist_alt_name)
                    or (reversed_artist and re.match(reversed_artist, artist_alt_name))
                )
            ) or (
                not case_sensitive
                and (
                    re.match(artist, artist_alt_name, re.IGNORECASE)
                    or (
                        reversed_artist
                        and (re.match(reversed_artist, artist_alt_name, re.IGNORECASE))
                    )
                )
            ):
                id_list.append(id)

    return id_list


def get_artist_names(artist_database, artist_id):

    """
    Return the list of names corresponding to an artist
    """

    return (
        artist_database[str(artist_id)]["names"]
        if str(artist_id) in artist_database
        else -1
    )


def get_groups_with_artist(artist_database, artist_id):

    """
    Return every group the artist is in (recursively)
    ie. Yuu Serizawa -> [Bunch, of, stuff, but, also, Prizmmy -> PrismBox]
    """

    grp_list = []
    for group in artist_database[str(artist_id)]["groups"]:
        if group[0] not in grp_list:
            grp_list.append(group[0])

    return grp_list


def get_artists_in_group(artist_database, group_id, alt_members_id=0):

    """
    Return a list of every artists in a group (recursively)
    ie. Prism Box -> [Prizmmy, list, of, member, in, prizmmy, W/E, list, of, member, in, w/e]
        TrySail -> [Sora Amamiya, Momo Asakura, Random]
        Kana Hanazawa -> [Kana Hanazawa]
    """

    artist_list = []
    if len(artist_database[str(group_id)]["members"]) > 0:
        for artist_id in artist_database[str(group_id)]["members"][alt_members_id]:
            artist_list += get_artists_in_group(artist_database, artist_id)
        return artist_list
    else:
        return [int(group_id)]


def separate_artists_list_by_comparing_with_another(
    another_artists_list, compared_artist_list
):

    """
    Input: Two list of artists_id
    Return two lists containing:
    - Every artist in compared_artist_list that are in another_artists_list
    - Every artist in compared_artist_list that are not in another_artists_list
    """

    is_in_artist_list = []
    is_not_in_artist_list = []

    for artist in compared_artist_list:
        if artist in another_artists_list:
            is_in_artist_list.append(artist)
        else:
            is_not_in_artist_list.append(artist)
    return is_in_artist_list, is_not_in_artist_list


def song_meets_search_requirement(
    artist_database,
    song,
    members_lists,
    group_granularity,
    max_other_artist,
    authorized_types,
):

    """
    Check that a song meets the group_granularity and the max_other_artist settings
    """

    if song["type"] in authorized_types:
        for members_list in members_lists:
            song_artist_list = []
            for artist in song["artist_ids"]:

                if (
                    group_granularity > 0
                    or len(members_list) == 1
                    and len(artist_database[str(members_list[0])]["members"]) < 1
                ):
                    song_artist_list += get_artists_in_group(
                        artist_database, artist[0], artist[1]
                    )
                else:
                    song_artist_list.append(artist[0])

            (
                is_in_artist_list,
                is_not_in_artist_list,
            ) = separate_artists_list_by_comparing_with_another(
                members_list, song_artist_list
            )

            tmp_group_granularity = max(
                min(group_granularity, len(members_list) - 1), 1
            )

            if len(is_in_artist_list) >= tmp_group_granularity:
                if len(is_not_in_artist_list) <= max_other_artist:
                    return True
    return False


def search_artist(
    song_database,
    artist_database,
    search,
    group_granularity=1,
    max_other_artist=3,
    ignore_special_character=True,
    partial_match=True,
    case_sensitive=False,
    max_nb_songs=250,
    authorized_types=[],
):

    """
    Return a list of songs corresponding to the search
    """

    artist_id_list = get_artist_id(
        artist_database, search, ignore_special_character, partial_match, case_sensitive
    )

    if len(artist_id_list) > 0:

        members_list = []
        for artist in artist_id_list:
            if group_granularity > 0:
                if len(artist_database[artist]["members"]) > 0:
                    for i in range(len(artist_database[artist]["members"])):
                        members_list.append(
                            get_artists_in_group(artist_database, artist, i)
                        )
                else:
                    members_list.append(get_artists_in_group(artist_database, artist))
                if int(artist) not in members_list[len(members_list) - 1]:
                    members_list[len(members_list) - 1].append(int(artist))
            else:
                members_list.append([int(artist)])

        song_list = []
        for anime in song_database:
            if len(song_list) >= max_nb_songs:
                break
            for song in anime["songs"]:
                if song_meets_search_requirement(
                    artist_database,
                    song,
                    members_list,
                    group_granularity,
                    max_other_artist,
                    authorized_types,
                ):
                    romaji = anime["romaji"] if "romaji" in anime.keys() else None
                    song_list.append(
                        utils.format_song(anime["annId"], anime["name"], romaji, song)
                    )

        return song_list

    else:
        return []


def search_artist_ids(
    song_database,
    artist_database,
    artist_ids,
    group_granularity,
    max_other_artist,
    max_nb_songs=250,
    authorized_types=[],
):

    """
    Return a list of songs corresponding to the search
    """

    if len(artist_ids) > 0:

        members_list = []
        for artist in artist_ids:
            if group_granularity > 0:
                members_list.append(get_artists_in_group(artist_database, artist))
                if int(artist) not in members_list[len(members_list) - 1]:
                    members_list[len(members_list) - 1].append(int(artist))
            else:
                members_list.append([int(artist)])

        print(members_list)

        song_list = []
        for anime in song_database:
            if len(song_list) >= max_nb_songs:
                break
            for song in anime["songs"]:
                if song_meets_search_requirement(
                    artist_database,
                    song,
                    members_list,
                    group_granularity,
                    max_other_artist,
                    authorized_types,
                ):
                    romaji = anime["romaji"] if "romaji" in anime.keys() else None
                    song_list.append(
                        utils.format_song(anime["annId"], anime["name"], romaji, song)
                    )

        return song_list

    else:
        return []
