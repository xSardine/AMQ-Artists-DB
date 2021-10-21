import sqlite3
from pathlib import Path
import functools

local_path = Path("data")
database_path = local_path / Path("Enhanced-AMQ-Database.db")


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


def connect_to_database(database_path):

    """
    Connect to the database and return the connection's cursor
    """

    try:
        sqliteConnection = sqlite3.connect(database_path)
        cursor = sqliteConnection.cursor()
        return cursor
    except sqlite3.Error as error:
        print("\n", error, "\n")
        exit(0)


def get_anime_info_from_anime_id(cursor, anime_id):

    """
    Return the content of animes table for that anime ID
    {
        annId
        english_name
        romaji_name
    }
    """

    command = "SELECT * FROM animes WHERE annId == ?;"
    anime = run_sql_command(cursor, command, [anime_id])[0]
    return {"annId": anime[0], "english_name": anime[1], "romaji_name": anime[2]}


def get_songs_ID_from_anime_ID(cursor, anime_id):

    """
    Return the list of songs ID linked to the anime ID
    """

    command = "SELECT song_id FROM link_anime_song WHERE anime_id == ?;"
    return {song[0] for song in run_sql_command(cursor, command, [anime_id])}


def get_song_info_from_song_ID(cursor, song_id):

    """
    Return the content of songs table for that song id
    {
        songId
        annSongId
        type
        number
        name
        artist
        720
        480
        mp3
    }
    """

    command = "SELECT * FROM songs WHERE id == ?;"
    song = run_sql_command(cursor, command, [song_id])[0]
    return {
        "songId": song[0],
        "annSongId": song[1],
        "type": song[2],
        "number": song[3],
        "name": song[4],
        "artist": song[5],
        "720": song[6],
        "480": song[7],
        "mp3": song[8],
    }


def get_song_artists_from_song_ID(cursor, song_id):

    """
    Return the list of (artists ID, id_of_set_of_artists) for that song id
    """

    command = "SELECT artist_id, artist_alt_members_id FROM link_song_artist WHERE song_id == ?;"
    return run_sql_command(cursor, command, [song_id])


def get_songs_with_artist_ID(cursor, artist_id):

    """
    Return every song ID that has the artist in it
    """

    command = "SELECT song_id FROM link_song_artist WHERE artist_id == ?;"
    return {song[0] for song in run_sql_command(cursor, command, [artist_id])}


def is_artist_a_group(cursor, artist_id):

    """
    Return True if the artist is a group
    Return False if not
    """

    command = "SELECT * FROM link_artist_group WHERE group_id == ?;"
    return True if run_sql_command(cursor, command, [artist_id]) else False


def get_members_list(cursor, artist_id, set_id=-1):

    """
    Return the list of artists presents in the couple (artist_id, artist_alt_members_id)
    I.E:    if set_id == -1: return every member for every version of the group
            else: list the members in that version of the group
    """
    if is_artist_a_group(cursor, artist_id):
        if set_id == -1:
            command = "SELECT artist_id FROM link_artist_group WHERE group_id == ?;"
            return {
                artist[0] for artist in run_sql_command(cursor, command, [artist_id])
            }
        else:
            command = "SELECT artist_id FROM link_artist_group WHERE group_id == ? AND group_alt_members_id == ?;"
            return {
                artist[0]
                for artist in run_sql_command(cursor, command, [artist_id, set_id])
            }
    else:
        return []


def get_groups_list(cursor, artist_id):

    """
    Return the list of groups the artist is in
    """

    command = "SELECT group_id, group_alt_members_id FROM link_artist_group WHERE artist_id == ?;"
    return run_sql_command(cursor, command, [artist_id])


def get_artist_names_from_artist_id(cursor, artist_id):

    """
    Return the list of names linked to the artist id
    """

    command = "SELECT name FROM artist_alt_names WHERE artist_id == ?;"
    return {name[0] for name in run_sql_command(cursor, command, [artist_id])}


def get_all_artistIds(cursor):

    """
    Return the ID of every artist in the DB
    """

    command = "SELECT DISTINCT id FROM artists;"
    return run_sql_command(cursor, command)


def get_all_annIDs(cursor):

    """
    Return every annID in the DB
    """

    command = "SELECT DISTINCT annId from animes;"
    return run_sql_command(cursor, command)


def get_all_songIds(cursor):
    """
    Return every songId in the DB
    """

    command = "SELECT DISTINCT id from songs;"
    return run_sql_command(cursor, command)


@functools.lru_cache(maxsize=1)
def extract_song_database():

    """
    Extract the song database
    """

    command = """
    SELECT animes.annId, animes.name, animes.romaji, songs.annSongId, songs.type, songs.number, 
    songs.name, songs.artist, songs."720p", songs."480p", songs.mp3, group_concat(link_song_artist.artist_id) 
    AS artists_ids, group_concat(link_song_artist.artist_alt_members_id) AS artists_ids_set
    FROM animes
    INNER JOIN songs ON animes.annId = songs.annId
    INNER JOIN link_song_artist ON songs.id = link_song_artist.song_id
    GROUP BY songs.id;
    """
    cursor = connect_to_database(database_path)
    song_database = []
    for song in run_sql_command(cursor, command):
        song_database.append(
            {
                "annId": song[0],
                "anime_eng_name": song[1],
                "anime_jp_name": song[2],
                "annSongId": song[3],
                "type": song[4],
                "number": song[5],
                "song_name": song[6],
                "artist": song[7],
                "720": song[8],
                "480": song[9],
                "mp3": song[10],
                "artists_ids": [
                    [int(id), int(set)]
                    for id, set in zip(song[11].split(","), song[12].split(","))
                ],
            }
        )
    return song_database


@functools.lru_cache(maxsize=1)
def extract_artist_database():

    """
    Extract the artist database
    """

    command = """
	SELECT artists.id, artists.name, group_concat(artist_alt_names.alt_name, "\$") AS alt_names, group_concat(link_artist_group.group_id) AS groups, 
    group_concat(link_artist_group.group_alt_config_id) AS groups_set
    FROM artists
    LEFT JOIN artist_alt_names ON artists.id = artist_alt_names.artist_id
    LEFT JOIN link_artist_group ON artists.id = link_artist_group.artist_id
    GROUP BY artists.id;
    """

    cursor = connect_to_database(database_path)
    artist_database = {}

    for artist in run_sql_command(cursor, command):

        groups = []
        if artist[3]:
            for id, sets in zip(artist[3].split(","), artist[4].split(",")):
                if [int(id), int(sets)] not in groups:
                    groups.append([int(id), int(sets)])

        artist_database[str(artist[0])] = {
            "name": artist[1],
            "alt_names": {name for name in artist[2].split("\\$")}
            if artist[2]
            else None,
            "groups": groups,
            "members": [],
        }

    for artist in artist_database:
        for group in artist_database[artist]["groups"]:
            while len(artist_database[str(group[0])]["members"]) <= group[1]:
                artist_database[str(group[0])]["members"].append(set())
            artist_database[str(group[0])]["members"][group[1]].add(int(artist))

    return artist_database
