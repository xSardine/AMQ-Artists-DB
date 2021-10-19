import json
from pathlib import Path

song_database = Path("../app/data/expand_mapping.json")

with open(song_database, encoding="utf-8") as json_file:
    song_database = json.load(json_file)

for anime in song_database:
    for song in anime["songs"]:
        if "Ann" in song["artist"]:
            print(anime["name"])
            print(song["annSongId"], end=" ")
            print(song["artist"])
            print()
