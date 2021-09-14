import re
from filters import utils


def get_artist_id(
    artist_database, artist, ignore_special_character, partial_match, case_sensitive
):

    """
    Return every artists corresponding to the filters
    """

    artist = utils.get_regex_search(artist, ignore_special_character, partial_match)

    id_list = []

    for id in artist_database.keys():
        for artist_alt_name in artist_database[id]:
            if (case_sensitive and re.match(artist, artist_alt_name)) or (
                not case_sensitive and re.match(artist, artist_alt_name, re.IGNORECASE)
            ):
                id_list.append(id)

    return id_list


def get_artist_names(artist_database, artist_id):

    """
    Return the list of names corresponding to an artist
    """

    artist_id = str(artist_id)
    return artist_database[artist_id] if artist_id in artist_database else "not found"


def get_groups_with_artist(group_database, artist_id):

    """
    Return every group the artist is in (recursively)
    ie. Yuu Serizawa -> [Bunch, of, stuff, but, also, Prizmmy -> PrismBox]
    """

    group_list = []
    for group in group_database:
        if str(artist_id) in group_database[group]:
            group_list.append(int(group))
            group_list += get_groups_with_artist(group_database, group)
    return group_list


def get_artists_in_group(group_database, group_id):

    """
    Return a list of every artists in a group (recursively)
    ie. Prism Box -> [Prizmmy, list, of, member, in, prizmmy, W/E, list, of, member, in, w/e]
        TrySail -> [Sora Amamiya, Momo Asakura, Random]
        Kana Hanazawa -> [Kana Hanazawa]
    """

    artist_list = []
    if str(group_id) in group_database.keys():
        for artist_id in group_database[str(group_id)]:
            artist_list += get_artists_in_group(group_database, artist_id)
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
    group_database,
    song,
    members_lists,
    group_granularity,
    max_other_artist,
    authorized_types,
):

    """
    Check that a song meets the groum_granularity and the max_other_artist settings
    """
    if song["type"] in authorized_types:
        for members_list in members_lists:
            song_artist_list = []
            for artist in song["artist_ids"]:
                song_artist_list += get_artists_in_group(group_database, artist)

            (
                is_in_artist_list,
                is_not_in_artist_list,
            ) = separate_artists_list_by_comparing_with_another(
                members_list, song_artist_list
            )

            tmp_group_granularity = max(
                min(group_granularity, len(members_list) - 1), 1
            )

            if "fripSide" in song["artist"]:
                print(members_list)
                print(song_artist_list)
                print()
                print("is in", is_in_artist_list)
                print("isn't", is_not_in_artist_list)
                print(max_other_artist)
                print(tmp_group_granularity)
                print()
                print()

            if len(is_in_artist_list) >= tmp_group_granularity:
                if len(is_not_in_artist_list) <= max_other_artist:
                    return True
    return False


def search_artist(
    song_database,
    artist_database,
    group_database,
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
                members_list.append(get_artists_in_group(group_database, artist))
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
                    group_database,
                    song,
                    members_list,
                    group_granularity,
                    max_other_artist,
                    authorized_types,
                ):
                    song_list.append(
                        utils.format_song(anime["annId"], anime["name"], song)
                    )

        return song_list

    else:
        return []
