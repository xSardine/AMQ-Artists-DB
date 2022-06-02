"""
Only kept for archive, not used anymore
"""


from pathlib import Path
import json
import sqlite3


"""
Add romaji names taken from the S/A scripts scrapping when Husa is playing
"""

source_file = Path("../data/preprocessed/FusedExpand.json")
mugi_db = Path("../data/source/songs.sqlite3")

with open(source_file, encoding="utf-8") as json_file:
    source_file = json.load(json_file)


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


try:
    sqliteConnection = sqlite3.connect(mugi_db)
    cursor = sqliteConnection.cursor()
    print("Connection successful :)")
except sqlite3.Error as error:
    print("\n", error, "\n")

command = "SELECT annid, anime from Songs where animeEnglish NOTNULL GROUP BY annid ORDER BY annid"

name_list = run_sql_command(cursor, command)

for name in name_list:
    for anime in source_file:
        if anime["annId"] == name[0]:
            anime["romaji"] = name[1]


with open("../data/preprocessed/FusedExpand2.json", "w", encoding="utf-8") as outfile:
    json.dump(source_file, outfile)
