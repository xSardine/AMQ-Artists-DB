import utils, sql_calls
from datetime import datetime
import timeit
from datetime import datetime
import re


def add_main_log(
    anime_search_filters,
    song_name_search_filters,
    artist_search_filters,
    composer_search_filters,
    and_logic,
    ignore_duplicate,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):

    print("-------------------------")

    print("Date: ", str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))),

    if isinstance(anime_search_filters, list):
        anime_search_filters = None

    if isinstance(song_name_search_filters, list):
        song_name_search_filters = None

    if isinstance(artist_search_filters, list):
        artist_search_filters = None

    if isinstance(composer_search_filters, list):
        composer_search_filters = None

    if (
        anime_search_filters
        and not isinstance(anime_search_filters, list)
        and song_name_search_filters
        and not isinstance(song_name_search_filters, list)
        and artist_search_filters
        and not isinstance(artist_search_filters, list)
        and composer_search_filters
        and not isinstance(composer_search_filters, list)
        and anime_search_filters.search == song_name_search_filters.search
        and song_name_search_filters.search == artist_search_filters.search
        and artist_search_filters.search == composer_search_filters.search
    ):
        print(f"Main filter: '{anime_search_filters.search}'")
    else:

        if anime_search_filters:
            print(f"Anime filter: '{anime_search_filters.search}'")
        if song_name_search_filters:
            print(f"Song Name filter: '{song_name_search_filters.search}'")
        if artist_search_filters:
            print(f"Artist filter: '{artist_search_filters.search}'")
        if composer_search_filters:
            print(f"Composer filter: '{composer_search_filters.search}'")

    print("Intersection: ", and_logic, end=" | ")
    print("Ignore Duplicates: ", ignore_duplicate, end=" | ")
    print("Types: ", authorized_types, end=" | ")
    print("Broadcasts: ", authorized_broadcasts, end=" | ")
    print("Song Categories: ", authorized_song_categories)

    return


def is_ranked_time():
    date = datetime.utcnow()
    # If ranked time UTC
    if (
        # CST
        (
            (date.hour == 1 and date.minute >= 30)
            or (date.hour == 2 and date.minute < 23)
        )
        # JST
        or (
            (date.hour == 11 and date.minute >= 30)
            or (date.hour == 12 and date.minute < 23)
        )
        # CET
        or (
            (date.hour == 18 and date.minute >= 30)
            or (date.hour == 19 and date.minute < 23)
        )
    ):
        return True
    return False


def get_duplicate_in_list(list, song):
    """
    Returns the index of the duplicate song in the list
    """

    for i, song2 in enumerate(list):
        if song[20] == song2["songName"] and song[22] == song2["songArtist"]:
            return i
    return -1


def combine_results(
    artist_database,
    annId_songs_list,
    anime_songs_list,
    songName_songs_list,
    artist_songs_list,
    composer_songs_list,
    and_logic=False,
    ignore_duplicate=False,
    max_nb_songs=500,
    anime_search_filters=None,
    song_name_search_filters=None,
    artist_search_filters=None,
    composer_search_filters=None,
):
    """
    Combine the results of the different search filters
    """

    annId_songs_list = [] if not annId_songs_list else annId_songs_list
    anime_songs_list = [] if not anime_songs_list else anime_songs_list
    songName_songs_list = [] if not songName_songs_list else songName_songs_list
    artist_songs_list = [] if not artist_songs_list else artist_songs_list
    composer_songs_list = [] if not composer_songs_list else composer_songs_list

    songId_done = []
    final_song_list = []
    for song in (
        annId_songs_list
        + anime_songs_list
        + songName_songs_list
        + artist_songs_list
        + composer_songs_list
    ):
        if max_nb_songs and len(final_song_list) >= max_nb_songs:
            break

        if song[13] in songId_done:
            continue

        duplicate_ID = get_duplicate_in_list(final_song_list, song)

        if and_logic:
            if (
                (
                    not artist_search_filters
                    or not artist_search_filters.search
                    or song in artist_songs_list
                )
                and (
                    not anime_search_filters
                    or not anime_search_filters.search
                    or song in anime_songs_list
                )
                and (
                    not song_name_search_filters
                    or not song_name_search_filters.search
                    or song in songName_songs_list
                )
                and (
                    not composer_search_filters
                    or not composer_search_filters.search
                    or song in composer_songs_list
                )
            ):
                if not ignore_duplicate or duplicate_ID == -1:
                    songId_done.append(song[13])
                    final_song_list.append(utils.format_song(artist_database, song))
                else:
                    if final_song_list[duplicate_ID]["annId"] > song[0]:
                        songId_done.append(song[13])
                        final_song_list[duplicate_ID] = utils.format_song(
                            artist_database, song
                        )
        else:
            if not ignore_duplicate or duplicate_ID == -1:
                songId_done.append(song[13])
                final_song_list.append(utils.format_song(artist_database, song))
            else:
                if final_song_list[duplicate_ID]["annId"] > song[0]:
                    songId_done.append(song[13])
                    final_song_list[duplicate_ID] = utils.format_song(
                        artist_database, song
                    )

    return final_song_list


def get_member_list_flat(art_database, artists, bottom=True):
    # If bottom: will skip subgroups and go directly to the lower tier possible

    member_list = []

    for artist, line_up in artists:
        if line_up == -1:
            member_list.append(int(artist))

        else:
            if not bottom:
                member_list.append(int(artist))

            for member in get_member_list_flat(
                art_database,
                art_database[str(artist)]["line_ups"][line_up]["members"],
                bottom=bottom,
            ):
                member_list.append(int(member))

    return member_list


def compare_two_artist_list(list1, list2):
    same_count = 0  # amount of people present in both
    add_count = 0  # additional people in list1 compared to list2

    for artist in list1:
        if artist not in list2:
            add_count += 1
        else:
            same_count += 1

    return same_count, add_count


def check_meets_artists_requirements(
    artist_database, song, artist_ids, group_granularity, max_other_artist
):

    # Exceptions for groups that have line ups, but also songs with no line ups : they should be considered both a group and artist
    LINE_UP_EXCEPTIONS = [
        33,  # Tokyo Konsei
        215,  # Suginami
        546,  # Pokemon Kids
        1736,  # JDK
        1639,  # System-B
        8086,  # IPD voice
        20185,  # School mates
        4261,
        7695,
        6678,
        5611,  # Uchuujin
    ]

    song_artists = [
        [artist, int(line_up)]
        for artist, line_up in zip(song[23].split(","), song[24].split(","))
    ]
    song_artists_flat = get_member_list_flat(artist_database, song_artists)

    for artist_id in artist_ids:

        line_ups = [[[str(artist_id), -1]]]

        artist = artist_database[str(artist_id)]

        if artist["line_ups"]:

            line_ups = [
                line_up["members"]
                for line_up in artist["line_ups"]
                if line_up["line_up_type"] == "vocalists"
            ]

            if artist_id in LINE_UP_EXCEPTIONS:
                line_ups += [[[str(artist_id), -1]]]

        for line_up in line_ups:

            checked_list = get_member_list_flat(artist_database, line_up)
            present_artist, additional_artist = compare_two_artist_list(
                song_artists_flat, checked_list
            )

            if (
                present_artist >= 1
                and additional_artist <= max_other_artist
                and present_artist >= min(group_granularity, len(line_up))
            ):
                return True

    return False


def check_meets_composers_requirements(
    artist_database,
    song,
    composer_ids,
    group_granularity,
    max_other_artist,
    arrangement,
):

    # Exceptions for groups that have line ups, but also songs with no line ups : they should be considered both a group and artist
    LINE_UP_EXCEPTIONS = [
        33,  # Tokyo Konsei
        215,  # Suginami
        546,  # Pokemon Kids
        1736,  # JDK
        1639,  # System-B
        8086,  # IPD voice
        20185,  # School mates
        4261,
        7695,
        6678,
        5611,  # Uchuujin
    ]

    song_composers = []
    if song[27]:
        song_composers += [
            [artist, int(line_up)]
            for artist, line_up in zip(song[27].split(","), song[28].split(","))
        ]
    if arrangement and song[31]:
        song_composers += [
            [artist, int(line_up)]
            for artist, line_up in zip(song[31].split(","), song[32].split(","))
        ]
    song_artists_flat = set(get_member_list_flat(artist_database, song_composers))

    for composer_id in composer_ids:

        line_ups = [[[str(composer_id), -1]]]

        artist = artist_database[str(composer_id)]

        if artist["line_ups"]:

            line_ups = [
                line_up["members"]
                for line_up in artist["line_ups"]
                # if line_up["line_up_type"] == "composers"  # TODO : add it once we start having more composer line up counterpart to normal groups
            ]

            # if composer_id in LINE_UP_EXCEPTIONS: TODO : add it once we start having more composer line up counterpart to normal groups
            line_ups += [[[str(composer_id), -1]]]  # TODO

        for line_up in line_ups:
            checked_list = get_member_list_flat(artist_database, line_up)
            present_artist, additional_artist = compare_two_artist_list(
                song_artists_flat, checked_list
            )

            if (
                present_artist >= 1
                and additional_artist <= max_other_artist
                and present_artist >= min(group_granularity, len(line_up))
            ):
                return True

    return False


def get_song_list_from_songIds_JSON(
    song_database,
    songIds,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):
    song_list = []

    for songId in songIds:

        if song_database[songId][16] not in authorized_types:
            continue

        if song_database[songId][18] not in authorized_song_categories:
            continue

        if (
            not song_database[songId][34] and not song_database[songId][35]
        ) and "Normal" not in authorized_broadcasts:
            continue

        if song_database[songId][34] and "Dub" not in authorized_broadcasts:
            if (
                not song_database[songId][35]
                or "Rebroadcast" not in authorized_broadcasts
            ):
                continue

        if song_database[songId][35] and "Rebroadcast" not in authorized_broadcasts:
            continue

        song_list.append(song_database[songId])

    return song_list


def get_all_groups(artist_id, artist_database, include_composers_groups=False):
    groups = []

    # TODO include_composers_groups do nothing yet, might be a problem in the long run to take into account composers groups

    # Get the groups for the current artist
    for group in artist_database[str(artist_id)]["groups"]:

        groups.append(group)

        # Recursively get the groups for the group itself
        group_id, _ = group
        groups += get_all_groups(group_id, artist_database, include_composers_groups)

    return groups


def process_artist(
    cursor,
    song_database,
    artist_database,
    search,
    partial_match,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
    group_granularity,
    max_other_artist,
):
    artist_search = utils.get_regex_search(search, partial_match, swap_words=True)

    artist_ids = sql_calls.get_artist_ids_from_regex(cursor, artist_search)

    # If no IDs found, fall back to indexing on songArtist string
    if not artist_ids:
        artist_songs_list = sql_calls.get_song_list_from_songArtist(
            cursor,
            artist_search,
            authorized_types,
            authorized_broadcasts,
            authorized_song_categories,
        )
        return artist_songs_list, artist_ids

    # TODO Reuse those process for future processes such as check meet requirement and post process of songs
    members = []
    if group_granularity != 0:
        if group_granularity > 0:
            for artist in artist_ids:
                if artist_database[str(artist)]["line_ups"]:
                    for line_up in artist_database[str(artist)]["line_ups"]:
                        for member in get_member_list_flat(
                            artist_database, line_up["members"], bottom=False
                        ):
                            if member not in members:
                                members.append(member)
                else:
                    members.append(artist)

    all_groups = []
    for artist in set(artist_ids + members):
        all_groups += get_all_groups(artist, artist_database)

    # Extract every song IDs containing an artist we have
    songIds = sql_calls.get_songs_ids_from_artist_ids(
        cursor,
        list(set(artist_ids + [group[0] for group in all_groups] + members)),
    )

    artist_songs_list = get_song_list_from_songIds_JSON(
        song_database,
        songIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    final_song_list = []
    for song in artist_songs_list:
        if check_meets_artists_requirements(
            artist_database,
            song,
            artist_ids,
            group_granularity,
            max_other_artist,
        ):
            final_song_list.append(song)

    return final_song_list, artist_ids


def process_composer(
    cursor,
    song_database,
    artist_database,
    search,
    partial_match,
    arrangement,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
    group_granularity,
    max_other_artist,
):

    composer_search = utils.get_regex_search(search, partial_match, swap_words=True)

    composer_ids = sql_calls.get_artist_ids_from_regex(cursor, composer_search)

    # If no IDs found, do not fall back to raw string for computing time
    if not composer_ids:
        return [], []

    # TODO Reuse those process for future processes such as check meet requirement and post process of songs
    members = []
    if group_granularity != 0:
        if group_granularity > 0:
            for artist in composer_ids:
                if artist_database[str(artist)]["line_ups"]:
                    for line_up in artist_database[str(artist)]["line_ups"]:
                        for member in get_member_list_flat(
                            artist_database, line_up["members"], bottom=False
                        ):
                            if member not in members:
                                members.append(member)
                else:
                    members.append(artist)

    all_groups = []
    for artist in set(composer_ids + members):
        all_groups += get_all_groups(artist, artist_database)

    # Extract every song IDs containing an artist we have
    songIds = sql_calls.get_songs_ids_from_composing_team_ids(
        cursor,
        composer_ids=list(
            set(composer_ids + [group[0] for group in all_groups] + members)
        ),
        arrangement=arrangement,
    )

    artist_songs_list = get_song_list_from_songIds_JSON(
        song_database,
        songIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    final_song_list = []
    for song in artist_songs_list:
        if check_meets_composers_requirements(
            artist_database,
            song,
            composer_ids,
            group_granularity,
            max_other_artist,
            arrangement,
        ):
            final_song_list.append(song)

    return final_song_list, composer_ids


def get_search_results(
    anime_search_filters,
    song_name_search_filters,
    artist_search_filters,
    composer_search_filters,
    and_logic,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):
    startstart = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    song_database = sql_calls.extract_song_database()
    anime_database = sql_calls.extract_anime_database()
    artist_database = sql_calls.extract_artist_database()

    add_main_log(
        anime_search_filters,
        song_name_search_filters,
        artist_search_filters,
        composer_search_filters,
        and_logic,
        ignore_duplicate,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    is_ranked = is_ranked_time()

    print(f"Preprocess: {round(timeit.default_timer() - startstart, 4)}", end=" | ")
    start = timeit.default_timer()

    # Filters to process only on main filter
    annId_songs_list = []
    if (
        anime_search_filters
        and song_name_search_filters
        and artist_search_filters
        and anime_search_filters.search == song_name_search_filters.search
        and song_name_search_filters.search == artist_search_filters.search
    ):
        # Links filter
        if False:
            songs = sql_calls.get_song_list_from_links(
                cursor, anime_search_filters.search
            )
            if songs:
                return [utils.format_song(artist_database, song) for song in songs]

        # annId Filter
        if str(anime_search_filters.search).isdigit():
            annId_songs_list = sql_calls.get_songs_list_from_annIds(
                cursor,
                [anime_search_filters.search],
                authorized_types,
                authorized_broadcasts,
                authorized_song_categories,
            )

    print(f"annId on Main: {round(timeit.default_timer() - start, 4)}", end=" | ")
    start = timeit.default_timer()

    # Anime Filter to process either way
    anime_songs_list = []
    if anime_search_filters:

        if len(anime_search_filters.search) <= 2:
            partial_match = False
        else:
            partial_match = anime_search_filters.partial_match

        anime_search = utils.get_regex_search(
            anime_search_filters.search, partial_match
        )

        anime_songs_list = []
        for annId in anime_database:
            anime = anime_database[annId]
            found = False

            for name in [anime["animeJPName"], anime["animeENName"]] + (
                anime["animeAltNames"].split("\$")
                if "animeAltNames" in anime and anime["animeAltNames"]
                else []
            ):
                if not name or found:
                    continue

                if re.match(anime_search, name.lower()):
                    found = True

            if found:
                for song in anime["songs"]:

                    if song[16] not in authorized_types:
                        continue

                    if song[18] not in authorized_song_categories:
                        continue

                    if (
                        not song[34] and not song[35]
                    ) and "Normal" not in authorized_broadcasts:
                        continue

                    if song[34] and "Dub" not in authorized_broadcasts:
                        if not song[35] or "Rebroadcast" not in authorized_broadcasts:
                            continue

                    if song[35] and "Rebroadcast" not in authorized_broadcasts:
                        continue

                    anime_songs_list.append(song)

    print(f"Anime: {round(timeit.default_timer() - start, 4)}", end=" | ")
    start = timeit.default_timer()

    # Song Name filter not available during ranked
    songName_songs_list = []
    if song_name_search_filters and not is_ranked:

        if len(song_name_search_filters.search) <= 2:
            partial_match = False
        else:
            partial_match = song_name_search_filters.partial_match

        songName_search = utils.get_regex_search(
            song_name_search_filters.search, partial_match
        )

        songName_songs_list = []
        for songId in song_database:
            song = song_database[songId]
            if re.match(songName_search, song[20].lower()):

                if song[16] not in authorized_types:
                    continue

                if song[18] not in authorized_song_categories:
                    continue

                if (
                    not song[34] and not song[35]
                ) and "Normal" not in authorized_broadcasts:
                    continue

                if song[34] and "Dub" not in authorized_broadcasts:
                    if not song[35] or "Rebroadcast" not in authorized_broadcasts:
                        continue

                if song[35] and "Rebroadcast" not in authorized_broadcasts:
                    continue

                songName_songs_list.append(song)

    print(f"Song Name: {round(timeit.default_timer() - start, 4)}", end=" | ")
    start = timeit.default_timer()

    # Artist filter not available during ranked
    artist_songs_list = []
    artist_ids = None

    if artist_search_filters and not is_ranked:

        if len(artist_search_filters.search) <= 2:
            partial_match = False
        else:
            partial_match = artist_search_filters.partial_match

        artist_songs_list, artist_ids = process_artist(
            cursor,
            song_database,
            artist_database,
            artist_search_filters.search,
            partial_match,
            authorized_types,
            authorized_broadcasts,
            authorized_song_categories,
            artist_search_filters.group_granularity,
            artist_search_filters.max_other_artist,
        )

    print(f"Artists: {round(timeit.default_timer() - start, 4)}", end=" | ")
    start = timeit.default_timer()

    # Composer filter not available during ranked
    composer_songs_list = []
    composer_ids = None

    if composer_search_filters and not is_ranked:

        if len(composer_search_filters.search) <= 2:
            partial_match = False
        else:
            partial_match = composer_search_filters.partial_match

        composer_songs_list, composer_ids = process_composer(
            cursor,
            song_database,
            artist_database,
            composer_search_filters.search,
            partial_match,
            composer_search_filters.arrangement,
            authorized_types,
            authorized_broadcasts,
            authorized_song_categories,
            composer_search_filters.group_granularity,
            composer_search_filters.max_other_artist,
        )

    print(f"Composers: {round(timeit.default_timer() - start, 4)}", end=" | ")
    start = timeit.default_timer()

    song_list = combine_results(
        artist_database,
        annId_songs_list,
        anime_songs_list,
        songName_songs_list,
        artist_songs_list,
        composer_songs_list,
        and_logic,
        ignore_duplicate,
        max_nb_songs,
        anime_search_filters=anime_search_filters,
        song_name_search_filters=song_name_search_filters,
        artist_search_filters=artist_search_filters,
        composer_search_filters=composer_search_filters,
    )

    print(f"Post Process: {round(timeit.default_timer() - start, 4)}", end=" | ")
    start = timeit.default_timer()

    computing_time = round(timeit.default_timer() - startstart, 4)
    nb_results = len(song_list)
    # TODO logs
    print(f"full_computing_time: {computing_time}", end=" | ")
    print(f"nb_results: {nb_results}")
    print()

    return song_list


def get_artists_ids_song_list(
    artist_ids,
    max_other_artist,
    group_granularity,
    ignore_duplicate,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):
    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    print("-------------------------")
    print("Date: ", str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    print(f"artist_id_filter: {artist_ids}")
    print(f"ignore_dups: {ignore_duplicate}", end=" | ")
    print(f"types: {authorized_types}", end=" | ")
    print(f"broadcasts: {authorized_broadcasts}", end=" | ")
    print(f"song_categories: {authorized_song_categories}")

    if not artist_ids:
        return []

    groups = []
    for artist in artist_ids:
        for group in artist_database[str(artist)]["groups"]:
            groups.append(group)

    songIds = sql_calls.get_songs_ids_from_artist_ids(
        cursor, list(set(artist_ids + [group[0] for group in groups]))
    )

    song_database = sql_calls.extract_song_database()

    songs = get_song_list_from_songIds_JSON(
        song_database,
        songIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    final_songs = []
    for song in songs:
        flag = False
        for artist, line_up in zip(song[23].split(","), song[24].split(",")):
            if int(artist) in artist_ids:
                flag = True
            for group, group_line_up in groups:
                if artist == group and int(line_up) == group_line_up:
                    flag = True
        if flag:
            final_songs.append(song)

    final_songs = combine_results(
        artist_database, final_songs, [], [], [], [], False, ignore_duplicate
    )

    stop = timeit.default_timer()

    print(f"computing_time: {round(stop - start, 4)}", end=" | ")
    print(f"nb_results: {len(songs)}")

    return final_songs


def get_composer_ids_song_list(
    composer_ids,
    arrangement,
    ignore_duplicate,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):
    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    print("-------------------------")
    print("Date: ", str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    print(f"composer_id_filter: {composer_ids}")
    print(f"ignore_dups: {ignore_duplicate}", end=" | ")
    print(f"types: {authorized_types}", end=" | ")
    print(f"broadcasts: {authorized_broadcasts}", end=" | ")
    print(f"song_categories: {authorized_song_categories}")

    if not composer_ids:
        return []

    groups = []
    for artist in composer_ids:
        for group in artist_database[str(artist)]["groups"]:
            groups.append(group)

    songIds = sql_calls.get_songs_ids_from_composing_team_ids(
        cursor, list(set(composer_ids + [group[0] for group in groups])), arrangement
    )

    song_database = sql_calls.extract_song_database()

    songs = get_song_list_from_songIds_JSON(
        song_database,
        songIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    final_songs = []
    for song in songs:
        flag = False
        for composer, line_up in zip(song[27].split(","), song[28].split(",")):
            if int(composer) in composer_ids:
                flag = True
            for group, group_line_up in groups:
                if composer == group and int(line_up) == group_line_up:
                    flag = True

        for arranger, line_up in zip(song[31].split(","), song[32].split(",")):
            if int(arranger) in composer_ids:
                flag = True
            for group, group_line_up in groups:
                if arranger == group and int(line_up) == group_line_up:
                    flag = True

        if flag:
            final_songs.append(song)

    final_songs = combine_results(
        artist_database, final_songs, [], [], [], [], False, ignore_duplicate
    )

    stop = timeit.default_timer()

    print(f"computing_time: {round(stop - start, 4)}", end=" | ")
    print(f"nb_results: {len(songs)}")

    return final_songs


def get_annId_song_list(
    annIds,
    ignore_duplicate,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):
    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    print("-------------------------")
    print("Date: ", str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    print(f"annId_filter: {annIds if len(annIds) < 5 else f'{len(annIds)} annIds'}")
    print(f"ignore_dups: {ignore_duplicate}", end=" | ")
    print(f"types: {authorized_types}", end=" | ")
    print(f"broadcasts: {authorized_broadcasts}", end=" | ")
    print(f"song_categories: {authorized_song_categories}")

    if len(annIds) == 0:
        return []

    if not all(str(annId).isdigit() for annId in annIds):
        return []

    songs = sql_calls.get_songs_list_from_annIds(
        cursor,
        annIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    songs = combine_results(
        artist_database,
        songs,
        [],
        [],
        [],
        [],
        False,
        ignore_duplicate,
        max_nb_songs=None,
    )

    stop = timeit.default_timer()

    print(f"computing_time: {round(stop - start, 4)}", end=" | ")
    print(f"nb_results: {len(songs)}")

    return songs


def get_malIds_song_list(
    malIds,
    ignore_duplicate,
    authorized_types=[1, 2, 3],
    authorized_broadcasts=["Normal", "Dub", "Rebroadcast"],
    authorized_song_categories=["Standard", "Chanting", "Instrumental", "Character"],
):

    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    print("-------------------------")
    print("Date: ", str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    print(f"malIds_filter: {len(malIds)}")
    print(f"ignore_dups: {ignore_duplicate}", end=" | ")
    print(f"types: {authorized_types}", end=" | ")
    print(f"broadcasts: {authorized_broadcasts}", end=" | ")
    print(f"song_categories: {authorized_song_categories}")

    for malId in malIds:
        if not str(malId).isdigit():
            return []

    songs = sql_calls.get_songs_list_from_malIds(
        cursor,
        malIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    if not songs:
        return []

    songs = combine_results(
        artist_database,
        songs,
        [],
        [],
        [],
        [],
        False,
        ignore_duplicate,
        max_nb_songs=None,
    )

    stop = timeit.default_timer()

    print(f"computing_time: {round(stop - start, 4)}", end=" | ")
    print(f"nb_results: {len(songs)}")

    return songs


def get_annSongIds_song_list(
    annSongIds,
    ignore_duplicate,
    authorized_types=[1, 2, 3],
    authorized_broadcasts=["Normal", "Dub", "Rebroadcast"],
    authorized_song_categories=["Standard", "Chanting", "Instrumental", "Character"],
):

    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    print("-------------------------")
    print("Date: ", str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    print(f"annSongIds_filter: {annSongIds if len(annSongIds) < 5 else f'{len(annSongIds)} annSongIds'}")
    print(f"ignore_dups: {ignore_duplicate}", end=" | ")
    print(f"types: {authorized_types}", end=" | ")
    print(f"broadcasts: {authorized_broadcasts}", end=" | ")
    print(f"song_categories: {authorized_song_categories}")

    if len(annSongIds) == 0:
        return []

    if not all(str(annSongId).isdigit() for annSongId in annSongIds):
        return []

    songs = sql_calls.get_songs_list_from_annSongIds(
        cursor,
        annSongIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    songs = combine_results(
        artist_database,
        songs,
        [],
        [],
        [],
        [],
        False,
        ignore_duplicate,
        max_nb_songs=None,
    )

    stop = timeit.default_timer()

    print(f"computing_time: {round(stop - start, 4)}", end=" | ")
    print(f"nb_results: {len(songs)}")

    return songs


def get_amqSongIds_song_list(
    amqSongIds,
    ignore_duplicate,
    authorized_types=[1, 2, 3],
    authorized_broadcasts=["Normal", "Dub", "Rebroadcast"],
    authorized_song_categories=["Standard", "Chanting", "Instrumental", "Character"],
):

    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    print("-------------------------")
    print("Date: ", str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    print(f"amqSongIds_filter: {amqSongIds if len(amqSongIds) < 5 else f'{len(amqSongIds)} amqSongIds'}")
    print(f"ignore_dups: {ignore_duplicate}", end=" | ")
    print(f"types: {authorized_types}", end=" | ")
    print(f"broadcasts: {authorized_broadcasts}", end=" | ")
    print(f"song_categories: {authorized_song_categories}")

    if len(amqSongIds) == 0:
        return []

    if not all(str(amqSongId).isdigit() for amqSongId in amqSongIds):
        return []

    songs = sql_calls.get_songs_list_from_amqSongIds(
        cursor,
        amqSongIds,
        authorized_types,
        authorized_broadcasts,
        authorized_song_categories,
    )

    songs = combine_results(
        artist_database,
        songs,
        [],
        [],
        [],
        [],
        False,
        ignore_duplicate,
        max_nb_songs=None,
    )

    stop = timeit.default_timer()

    print(f"computing_time: {round(stop - start, 4)}", end=" | ")
    print(f"nb_results: {len(songs)}")

    return songs
