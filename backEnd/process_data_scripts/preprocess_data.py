import sqlite3
import json
from pathlib import Path

"""
Fuse the expand data with the MugiBotDatabase
"""

database = Path("../data/source/MugiBotDatbase.db")
source_input_file = Path("../data/source/expand.json")
output_path = Path("../data/preprocessed")

output_path.mkdir(parents=False, exist_ok=True)


def run_sql_command(cursor, sql_command, data):

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


try:
    sqliteConnection = sqlite3.connect(database)
    cursor = sqliteConnection.cursor()
    command = "SELECT Show, Type, SongName, Artist, MP3, _720, _480, AnnID FROM SongTableObject WHERE AnnSongID = 0 OR AnnSongID = -1"
    data = run_sql_command(cursor, command, [])
    not_in_expand = []
    for song in data:
        if song[7] not in [anime["annId"] for anime in not_in_expand]:
            not_in_expand.append({"annId": song[7], "name": song[0], "songs": []})
        for anime in not_in_expand:
            if song[7] == anime["annId"]:
                if song[1].startswith("Opening"):
                    type = 1
                    if len(song[1]) <= 9:
                        number = int(song[1][-1])
                    else:
                        number = int(song[1][-2:])
                elif song[1].startswith("Ending"):
                    type = 2
                    if len(song[1]) <= 8:
                        number = int(song[1][-1])
                    else:
                        number = int(song[1][-2:])
                else:
                    type = 3
                    number = 0
                anime["songs"].append(
                    {
                        "annSongId": -1,
                        "name": song[2],
                        "type": type,
                        "number": number,
                        "artist": song[3],
                        "examples": {"480": song[6], "720": song[5], "mp3": song[4]},
                    }
                )

    with open(output_path / Path("notExpand.json"), "w", encoding="utf-8") as outfile:
        json.dump(not_in_expand, outfile)

    with open(source_input_file, encoding="utf-8") as json_file:
        data = json.load(json_file)["questions"]

        for anime in data:
            for song in anime["songs"]:
                song.pop("versions", None)
        for anime in not_in_expand:
            flag_done = False
            for anime2 in data:
                if anime["annId"] == anime2["annId"]:
                    for song in anime["songs"]:
                        anime2["songs"].append(song)
                    flag_done = True
                    break
            if not flag_done:
                data.append(anime)

    with open(
        output_path / Path("FusedExpand2.json"), "w", encoding="utf-8"
    ) as outfile:
        json.dump(data, outfile)

except sqlite3.Error as error:
    print("\n", error, "\n")

