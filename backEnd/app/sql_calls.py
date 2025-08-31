import sqlite3, re
from pathlib import Path
from functools import lru_cache
import timeit

local_path = Path("data")
database_path = local_path / Path("Enhanced-AMQ-Database.db")


@lru_cache(maxsize=None)
def extract_song_database():
    """
    Extract the song database
    """

    command = """
    SELECT * FROM songsFull;
    """

    cursor = connect_to_database(database_path)

    song_database = {}
    for song in run_sql_command(cursor, command):
        song_database[song[13]] = song

    return song_database


@lru_cache(maxsize=None)
def extract_anime_database():
    """
    Extract the song database
    """

    command = """
    SELECT * FROM songsFull;
    """

    cursor = connect_to_database(database_path)

    anime_database = {}
    for song in run_sql_command(cursor, command):
        if song[0] not in anime_database:
            anime_database[song[0]] = {
                "animeJPName": song[6],
                "animeENName": song[7],
                "animeAltNames": song[9],
                "animeVintage": song[10],
                "animeType": song[11],
                "animeCategory": song[12],
                "songs": [],
            }
        anime_database[song[0]]["songs"].append(song)

    return anime_database


@lru_cache(maxsize=None)
def extract_artist_database():
    """
    Extract the artist database
    """

    cursor = connect_to_database(database_path)

    extract_basic_info = """
    SELECT id, romaji_names, disambiguation, type FROM artistsNames
    """

    basic_info = run_sql_command(cursor, extract_basic_info)

    extract_artist_groups = """
    SELECT id, groups, groups_line_up FROM artistsGroups
    """

    artist_groups = run_sql_command(cursor, extract_artist_groups)

    extract_line_up_members = """
    SELECT artist_id, line_up_id, line_up_type, members, members_line_up FROM lineUpsMembers
    """

    line_ups_members = run_sql_command(cursor, extract_line_up_members)

    if len(basic_info) != len(artist_groups):
        print("ERROR EXTRACTING ARTIST DATABASE")
        return {}

    artist_database = {}
    for info, groups in zip(basic_info, artist_groups):
        if info[0] != groups[0]:
            print("ERROR EXTRACTING ARTIST DATABASE")
            return {}

        artist_database[str(info[0])] = {
            "names": info[1].split("\\$"),
            "groups": (
                [
                    [group, int(line_up)]
                    for group, line_up in zip(
                        groups[1].split(","), groups[2].split(",")
                    )
                ]
                if groups[1]
                else []
            ),
            "line_ups": [],
            "disambiguation": info[2],
            "type": info[3],
        }

    for line_up_members in line_ups_members:

        artist = artist_database[str(line_up_members[0])]

        # retrieve info from the artist
        for info in basic_info:
            if info[0] == line_up_members[0]:
                break

        if info[0] != line_up_members[0]:
            print(f"ERROR EXTRACTING ARTIST DATABASE on {line_up_members[0]}")
            return {}

        if line_up_members[1] != len(artist["line_ups"]):
            print(f"ERROR EXTRACTING ARTIST DATABASE on {line_up_members[0]}")
            return {}

        current_lu = []
        for member_id, member_line_up_id in zip(
            line_up_members[3].split(","), line_up_members[4].split(",")
        ):
            current_lu.append([member_id, int(member_line_up_id)])

        artist["line_ups"].append(
            {
                "line_up_type": line_up_members[2],
                "members": current_lu,
            }
        )

    return artist_database


def run_sql_command(cursor, sql_command, data=None):
    """
    Run the SQL command with nice looking print when failed (no)
    """

    try:
        if data is not None:
            cursor.execute(sql_command, data)
        else:
            cursor.execute(sql_command)

        record = cursor.fetchall()

        return record

    except sqlite3.Error as error:
        if data is not None:
            for param in data:
                if type(param) == str:
                    sql_command = sql_command.replace("?", '"' + str(param) + '"', 1)
                else:
                    sql_command = sql_command.replace("?", str(param), 1)

        print(
            "\nError while running this command: \n",
            sql_command,
            "\n",
            error,
            "\nData: ",
            data,
            "\n",
        )
        return None


def regexp(expr, item):
    try:
        reg = re.compile(expr)
        return reg.search(item) is not None
    except Exception as e:
        pass


def connect_to_database(database_path):
    """
    Connect to the database and return the connection's cursor
    """

    try:
        sqliteConnection = sqlite3.connect(database_path)
        sqliteConnection.create_function("REGEXP", 2, regexp)
        cursor = sqliteConnection.cursor()
        return cursor
    except sqlite3.Error as error:
        print("\n", error, "\n")
        exit(0)


def build_broadcast_filter(authorized_broadcasts):
    """
    Build SQL WHERE clause for broadcast filtering.
    
    Args:
        authorized_broadcasts: List of allowed broadcast types ("Normal", "Dub", "Rebroadcast")
    
    Returns:
        str: SQL WHERE clause fragment for broadcast filtering
        
    Examples:
        - ["Normal", "Dub", "Rebroadcast"] -> "" (no filtering)
        - ["Normal", "Dub"] -> " AND isRebroadcast == 0"
        - ["Normal"] -> " AND isDub == 0 AND isRebroadcast == 0"
        - ["Dub", "Rebroadcast"] -> " AND (isDub == 1 OR isRebroadcast == 1)"
    """
    if not authorized_broadcasts:
        return ""
    
    conditions = []
    
    # Normal broadcasts: isDub == 0 AND isRebroadcast == 0
    if "Normal" not in authorized_broadcasts:
        conditions.append("(isDub == 1 OR isRebroadcast == 1)")
    
    # Dub broadcasts: isDub == 1
    if "Dub" not in authorized_broadcasts:
        conditions.append("isDub == 0")
    
    # Rebroadcast broadcasts: isRebroadcast == 1
    if "Rebroadcast" not in authorized_broadcasts:
        conditions.append("isRebroadcast == 0")
    
    if not conditions:
        return ""
    
    return " AND " + " AND ".join(conditions)


def get_songs_list_from_ann_ids(
    cursor,
    ann_ids,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):

    broadcast_filter = build_broadcast_filter(authorized_broadcasts)

    get_songs_from_annId = f"SELECT * from songsFull WHERE songType IN ({','.join('?'*len(authorized_types))}) AND annId IN ({','.join('?'*len(ann_ids))}) {broadcast_filter} AND songCategory IN ({','.join('?'*len(authorized_song_categories))})"

    return run_sql_command(
        cursor,
        get_songs_from_annId,
        authorized_types + ann_ids + authorized_song_categories,
    )


def get_songs_list_from_mal_ids(
    cursor,
    mal_ids,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):

    broadcast_filter = build_broadcast_filter(authorized_broadcasts)

    get_songs_from_malIds = f"SELECT * from songsFull WHERE songType IN ({','.join('?'*len(authorized_types))}) AND malId IN ({','.join('?'*len(mal_ids))}) {broadcast_filter} AND songCategory IN ({','.join('?'*len(authorized_song_categories))})"
    return run_sql_command(
        cursor,
        get_songs_from_malIds,
        authorized_types + mal_ids + authorized_song_categories,
    )


def get_songs_list_from_ann_song_ids(
    cursor,
    ann_song_ids,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):

    broadcast_filter = build_broadcast_filter(authorized_broadcasts)

    get_songs_from_annSongIds = f"SELECT * from songsFull WHERE songType IN ({','.join('?'*len(authorized_types))}) AND annSongId IN ({','.join('?'*len(ann_song_ids))}) {broadcast_filter} AND songCategory IN ({','.join('?'*len(authorized_song_categories))})"
    return run_sql_command(
        cursor,
        get_songs_from_annSongIds,
        authorized_types + ann_song_ids + authorized_song_categories,
    )


def get_songs_list_from_amq_song_ids(
    cursor,
    amq_song_ids,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):

    broadcast_filter = build_broadcast_filter(authorized_broadcasts)

    get_songs_from_amqSongIds = f"SELECT * from songsFull WHERE songType IN ({','.join('?'*len(authorized_types))}) AND amqSongId IN ({','.join('?'*len(amq_song_ids))}) {broadcast_filter} AND songCategory IN ({','.join('?'*len(authorized_song_categories))})"
    return run_sql_command(
        cursor,
        get_songs_from_amqSongIds,
        authorized_types + amq_song_ids + authorized_song_categories,
    )


def get_song_list_from_songArtist(
    cursor, regex, authorized_types, authorized_broadcasts, authorized_song_categories
):
    # TODO Indexes on lower ?

    broadcast_filter = build_broadcast_filter(authorized_broadcasts)

    get_song_list_from_songArtist = f"SELECT * from songsFull WHERE songType IN ({','.join('?'*len(authorized_types))}) {broadcast_filter} AND songCategory IN ({','.join('?'*len(authorized_song_categories))}) AND lower(romajiSongArtist) REGEXP ? LIMIT 500"
    return run_sql_command(
        cursor,
        get_song_list_from_songArtist,
        authorized_types + authorized_song_categories + [regex],
    )


def get_songs_ids_from_artist_ids(cursor, artist_ids):
    get_songs_ids_from_artist_ids = f"SELECT song_id from link_song_artist WHERE artist_id IN ({','.join('?'*len(artist_ids))})"
    return [
        id[0]
        for id in run_sql_command(
            cursor, get_songs_ids_from_artist_ids, [str(id) for id in artist_ids]
        )
    ]


def get_songs_ids_from_composing_team_ids(cursor, composer_ids, arrangement):
    # TODO FIND A BETTER WAY WITH VIEW
    get_songs_ids_from_composer_ids = f"SELECT song_id from link_song_composer WHERE composer_id IN ({','.join('?'*len(composer_ids))}) LIMIT 500"
    songIds = set()
    for song_id in run_sql_command(
        cursor, get_songs_ids_from_composer_ids, composer_ids
    ):
        songIds.add(song_id[0])

    if arrangement:
        get_songs_ids_from_arranger_ids = f"SELECT song_id from link_song_arranger WHERE arranger_id IN ({','.join('?'*len(composer_ids))}) LIMIT 500"
        for song_id in run_sql_command(
            cursor, get_songs_ids_from_arranger_ids, composer_ids
        ):
            songIds.add(song_id[0])

    songIds = list(songIds)

    return songIds


def get_artist_ids_from_regex(cursor, regex):
    # TODO Index on lower ?
    get_artist_ids_from_regex = "SELECT artist_id from link_artist_name WHERE lower(romaji_name) REGEXP ? GROUP BY artist_id LIMIT 50"
    artist_ids = [
        id[0] for id in run_sql_command(cursor, get_artist_ids_from_regex, [regex])
    ]
    return artist_ids


def get_song_list_from_links(cursor, link):
    if "catbox.moe" not in link or (".webm" not in link and ".mp3" not in link):
        return []

    link = f".*{link}.*"

    # TODO Indexes ?
    get_songs_from_link = (
        f"SELECT * from songsFull WHERE HQ REGEXP ? OR MQ REGEXP ? OR audio REGEXP ?"
    )
    songs = run_sql_command(cursor, get_songs_from_link, [link, link, link])
    return songs


def get_artist_names_from_artist_id(cursor, artist_id):
    """
    Return the list of names linked to the artist id as a dict
    """

    command = "SELECT names FROM artistsNames WHERE id == ?;"

    result = run_sql_command(cursor, command, [int(artist_id)])[0][0].split("\\$")

    return result


def get_artist_line_ups(cursor, artist_id):
    command = f"SELECT * FROM artistsLineUps WHERE id = {artist_id}"
    return run_sql_command(cursor, command)


def get_artist_groups(cursor, artist_id):
    command = f"SELECT * FROM artistsGroups WHERE id = {artist_id}"
    groups = run_sql_command(cursor, command)[0]
    if not groups[1]:
        return []
    else:
        return [
            [group, line_up]
            for group, line_up in zip(groups[1].split(","), groups[2].split(","))
        ]


def get_songs_list_from_season(
    cursor,
    season,
    authorized_types,
    authorized_broadcasts,
    authorized_song_categories,
):
    """
    Get songs from a specific season with proper broadcast filtering.
    Uses the same broadcast filtering logic as other functions in this module.
    """
    # Build the SQL query with filters
    base_query = "SELECT * from songsFull WHERE animeVintage LIKE ?"
    params = [f"%{season}%"]
    
    # Add song type filter
    if authorized_types:
        type_placeholders = ",".join(["?"] * len(authorized_types))
        base_query += f" AND songType IN ({type_placeholders})"
        params.extend(authorized_types)
    
    # Add broadcast type filter
    broadcast_filter = build_broadcast_filter(authorized_broadcasts)
    base_query += broadcast_filter
    
    # Add song category filter
    if authorized_song_categories:
        category_placeholders = ",".join(["?"] * len(authorized_song_categories))
        base_query += f" AND songCategory IN ({category_placeholders})"
        params.extend(authorized_song_categories)

    return run_sql_command(cursor, base_query, params)
