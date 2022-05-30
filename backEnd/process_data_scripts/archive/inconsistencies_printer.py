"""
Print inconsistencies to give to and try to force mods to fix
"""

import json
from pathlib import Path
import process_artists.config1_exceptions

song_database = Path("../app/data/expand_mapping.json")

with open(song_database, encoding="utf-8") as json_file:
    song_database = json.load(json_file)

for exception in process_artists.config1_exceptions.alternative_names:
    for alt_name in exception:
        print(f'"{alt_name}"', end=" ")
        for anime in song_database:
            id_list = set()
            for song in anime["songs"]:
                if alt_name in song["artist"]:
                    id_list.add(anime["annId"])
            for id in id_list:
                print(id, end=" ")
        print()
    print()
