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
):

    logs = {
        "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
    }

    if anime_search_filters:
        logs["anime_filter"] = {
            "search": anime_search_filters.search,
            "partial_match": anime_search_filters.partial_match,
        }
    if song_name_search_filters:
        logs["song_filter"] = {
            "search": song_name_search_filters.search,
            "partial_match": song_name_search_filters.partial_match,
        }
    if artist_search_filters:
        logs["artist_filter"] = {
            "search": artist_search_filters.search,
            "partial_match": artist_search_filters.partial_match,
            "group_granularity": artist_search_filters.group_granularity,
            "max_other_people": artist_search_filters.max_other_artist,
        }
    if composer_search_filters:
        logs["composer_filter"] = {
            "search": composer_search_filters.search,
            "partial_match": composer_search_filters.partial_match,
            "arrangement": composer_search_filters.arrangement,
        }
    logs["is_intersection"] = and_logic
    logs["ignore_dups"] = ignore_duplicate
    logs["types"] = authorized_types

    for key in logs:
        print(f"{key}: {logs[key]}")

    print()
    # TODO
    return


def is_ranked_time():

    date = datetime.utcnow()
    # If ranked time UTC
    if (
        # CST
        (
            (date.hour == 1 and date.minute >= 30)
            or (date.hour == 2 and date.minute <= 30)
        )
        # JST
        or (
            (date.hour == 11 and date.minute >= 30)
            or (date.hour == 12 and date.minute <= 30)
        )
        # CET
        or (
            (date.hour == 18 and date.minute >= 30)
            or (date.hour == 19 and date.minute <= 30)
        )
    ):
        return True
    return False


def get_duplicate_in_list(list, song):
    for i, song2 in enumerate(list):
        if song[10] == song2["songName"] and song[11] == song2["songArtist"]:
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
    max_nb_songs=300,
):

    songId_done = []
    final_song_list = []
    for song in (
        annId_songs_list
        + anime_songs_list
        + songName_songs_list
        + artist_songs_list
        + composer_songs_list
    ):

        if len(final_song_list) >= max_nb_songs:
            break

        if song[6] in songId_done:
            continue

        duplicate_ID = get_duplicate_in_list(final_song_list, song)
        if and_logic:
            if (
                (not artist_songs_list or song in artist_songs_list)
                and (not anime_songs_list or song in anime_songs_list)
                and (not songName_songs_list or song in songName_songs_list)
                and (not composer_songs_list or song in composer_songs_list)
            ):
                if not ignore_duplicate or duplicate_ID == -1:
                    songId_done.append(song[6])
                    final_song_list.append(utils.format_song(artist_database, song))
                else:
                    if final_song_list[duplicate_ID]["annId"] > song[0]:
                        songId_done.append(song[6])
                        final_song_list[duplicate_ID] = utils.format_song(
                            artist_database, song
                        )
        else:
            if not ignore_duplicate or duplicate_ID == -1:
                songId_done.append(song[6])
                final_song_list.append(utils.format_song(artist_database, song))
            else:
                if final_song_list[duplicate_ID]["annId"] > song[0]:
                    songId_done.append(song[6])
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
                art_database[str(artist)]["members"][line_up],
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

    song_artists = [
        [artist, int(line_up)]
        for artist, line_up in zip(song[12].split(","), song[13].split(","))
    ]
    song_artists_flat = get_member_list_flat(artist_database, song_artists)

    for artist_id in artist_ids:

        line_ups = [[[str(artist_id), -1]]]
        if artist_database[str(artist_id)]["members"]:
            line_ups = artist_database[str(artist_id)]["members"]

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


def get_song_list_from_songIds_JSON(song_database, songIds, authorized_types):

    song_list = []

    for songId in songIds:
        if song_database[songId][8] in authorized_types:
            song_list.append(song_database[songId])

    return song_list


def process_artist(
    cursor,
    song_database,
    artist_database,
    search,
    partial_match,
    authorized_types,
    group_granularity,
    max_other_artist,
):

    artist_search = utils.get_regex_search(search, partial_match, swap_words=True)

    artist_ids = sql_calls.get_artist_ids_from_regex(cursor, artist_search)

    # If no IDs found, fall back to indexing on songArtist string
    if not artist_ids:
        artist_songs_list = sql_calls.get_song_list_from_songArtist(
            cursor, artist_search, authorized_types
        )
        return artist_songs_list, artist_ids

    # TODO Reuse those process for future processes such as check meet requirement and post process of songs
    members = []
    if group_granularity != 0:
        if group_granularity > 0:
            for artist in artist_ids:
                if artist_database[str(artist)]["members"]:
                    for line_up in artist_database[str(artist)]["members"]:
                        for member in get_member_list_flat(
                            artist_database, line_up, bottom=False
                        ):
                            if member not in members:
                                members.append(member)
                else:
                    members.append(artist)

    groups = []
    for artist in list(set(artist_ids + members)):
        for group in artist_database[str(artist)]["groups"]:
            groups.append(group)

    # Extract every song IDs containing an artist we have
    songIds = sql_calls.get_songs_ids_from_artist_ids(
        cursor,
        list(set(artist_ids + [group[0] for group in groups] + members)),
    )

    artist_songs_list = get_song_list_from_songIds_JSON(
        song_database, songIds, authorized_types
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


def get_search_results(
    anime_search_filters,
    song_name_search_filters,
    artist_search_filters,
    composer_search_filters,
    and_logic,
    ignore_duplicate,
    max_nb_songs,
    authorized_types,
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
    )

    is_ranked = is_ranked_time()

    print(f"Preprocess: {round(timeit.default_timer() - startstart, 4)}")
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

        # Links filter not available during ranked
        if not is_ranked:
            songs = sql_calls.get_song_list_from_links(
                cursor, anime_search_filters.search
            )
            if songs:
                return [utils.format_song(artist_database, song) for song in songs]

        # annId Filter
        if str(anime_search_filters.search).isdigit():
            annId_songs_list = sql_calls.get_songs_list_from_annIds(
                cursor, [anime_search_filters.search], authorized_types
            )

    print(f"annId on Main: {round(timeit.default_timer() - start, 4)}")
    start = timeit.default_timer()

    # Anime Filter to process either way
    anime_songs_list = []
    if anime_search_filters:

        anime_search = utils.get_regex_search(
            anime_search_filters.search, anime_search_filters.partial_match
        )

        anime_songs_list = []
        for annId in anime_database:
            anime = anime_database[annId]
            if not anime["animeJPName"]:
                if re.match(anime_search, anime["animeExpandName"].lower()):
                    for song in anime["songs"]:
                        if song[8] in authorized_types:
                            anime_songs_list.append(song)
            else:
                if re.match(anime_search, anime["animeJPName"].lower()) or re.match(
                    anime_search, anime["animeENName"].lower()
                ):
                    for song in anime["songs"]:
                        if song[8] in authorized_types:
                            anime_songs_list.append(song)

    print(f"Anime: {round(timeit.default_timer() - start, 4)}")
    start = timeit.default_timer()

    # Song Name filter not available during ranked
    songName_songs_list = []
    if song_name_search_filters and not is_ranked:

        songName_search = utils.get_regex_search(
            song_name_search_filters.search, song_name_search_filters.partial_match
        )

        songName_songs_list = []
        for songId in song_database:
            song = song_database[songId]
            if song[8] in authorized_types and re.match(
                songName_search, song[10].lower()
            ):
                songName_songs_list.append(song)

    print(f"Song Name: {round(timeit.default_timer() - start, 4)}")
    start = timeit.default_timer()

    # Artist filter not available during ranked
    artist_songs_list = []
    artist_ids = None

    if artist_search_filters and not is_ranked:

        artist_songs_list, artist_ids = process_artist(
            cursor,
            song_database,
            artist_database,
            artist_search_filters.search,
            artist_search_filters.partial_match,
            authorized_types,
            artist_search_filters.group_granularity,
            artist_search_filters.max_other_artist,
        )

    print(f"Artists: {round(timeit.default_timer() - start, 4)}")
    start = timeit.default_timer()

    # Composer filter not available during ranked
    composer_songs_list = []
    if composer_search_filters and not is_ranked:

        if (
            not artist_search_filters
            or composer_search_filters.search != artist_search_filters.search
        ):

            artist_search = utils.get_regex_search(
                composer_search_filters.search,
                composer_search_filters.partial_match,
                swap_words=True,
            )
            artist_ids = sql_calls.get_artist_ids_from_regex(cursor, artist_search)

        if artist_ids:

            songIds = sql_calls.get_songs_ids_from_composing_team_ids(
                cursor, artist_ids, composer_search_filters.arrangement
            )

            composer_songs_list = get_song_list_from_songIds_JSON(
                song_database, songIds, authorized_types
            )

    print(f"Composers: {round(timeit.default_timer() - start, 4)}")
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
    )

    print(f"Post Process: {round(timeit.default_timer() - start, 4)}")
    start = timeit.default_timer()

    computing_time = round(timeit.default_timer() - startstart, 4)
    nb_results = len(song_list)
    # TODO logs
    print(f"full_computing_time: {computing_time}")
    print(f"nb_results: {nb_results}")
    print()

    return song_list


def get_artists_ids_song_list(
    artist_ids,
    max_other_artist,
    group_granularity,
    ignore_duplicate,
    authorized_types,
):

    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    logs = {
        "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        "artist_ids_filter": artist_ids,
        "ignore_dups": ignore_duplicate,
        "types": authorized_types,
    }
    for key in logs:
        print(f"{key}: {logs[key]}")

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

    songs = get_song_list_from_songIds_JSON(song_database, songIds, authorized_types)

    final_songs = []
    for song in songs:
        flag = False
        for artist, line_up in zip(song[12].split(","), song[13].split(",")):
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

    print()
    logs["computing_time"] = round(stop - start, 4)
    logs["nb_results"] = len(songs)
    print(f"computing_time: {logs['computing_time']}")
    print(f"nb_results: {logs['nb_results']}")
    print()

    return final_songs


def get_annId_song_list(
    annId,
    ignore_duplicate,
    authorized_types,
):

    start = timeit.default_timer()

    cursor = sql_calls.connect_to_database(sql_calls.database_path)

    artist_database = sql_calls.extract_artist_database()

    logs = {
        "date": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        "annId_filter": annId,
        "ignore_dups": ignore_duplicate,
        "types": authorized_types,
    }

    for key in logs:
        print(f"{key}: {logs[key]}")

    if not str(annId).isdigit():
        return []

    songs = sql_calls.get_songs_list_from_annIds(cursor, [annId], authorized_types)

    songs = combine_results(
        artist_database, songs, [], [], [], [], False, ignore_duplicate
    )

    stop = timeit.default_timer()

    logs["computing_time"] = round(stop - start, 4)
    logs["nb_results"] = len(songs)
    print(f"full time: {logs['computing_time']}")
    print(f"nb_results: {logs['nb_results']}")
    print()

    return songs
