from pathlib import Path
import json


"""
Check for potential duplicates coming from the Mugibot Database
"""

source_file = Path("../data/preprocessed/FusedExpand.json")
romaji_file = Path("../data/source/songs.sqlite3")


with open(source_file, encoding="utf-8") as json_file:
    source_file = json.load(json_file)

for anime in source_file:
    for i, song1 in enumerate(anime["songs"]):
        for j, song2 in enumerate(anime["songs"]):
            if (
                i != j
                and song1["annSongId"] == -1
                and song1["type"] == song2["type"]
                and song1["number"] == song2["number"]
            ):
                print("might be duplicated:")
                print(song1["name"], "-->", song2["name"])
                print(i, j)
                print()
