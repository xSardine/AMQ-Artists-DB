import json
from pathlib import Path
import config5_composers

song_database_path = Path("../../public/data/expand_mapping.json")
artist_database_path = Path("../../public/data/artist_mapping.json")

with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)

composers = config5_composers.composers


def get_artist_id(artist_ids_mapping, artist, warning=False):

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]["names"]:
            if artist_alt_name == artist:
                return id
    if not warning:
        print(artist, "not found... adding it")
    else:
        print("\n", "WARNING: GROUP NAME", artist, "DOES NOT EXIST: WARNING", "\n")
    id = len(artist_ids_mapping.keys())
    artist_ids_mapping[id] = {"names": [artist], "groups": [], "members": []}
    return id


for composer in composers:

    composer_id = get_artist_id(artist_database, composer["name"], warning=True)

    for anime in song_database:
        for song in anime["songs"]:
            if "composer_ids" not in song:
                song["composer_ids"] = []
            for artist_id in song["artist_ids"]:
                if int(artist_id[0]) == int(composer_id):
                    song["composer_ids"].append(int(composer_id))
                    print(song)
                    print()

with open(song_database_path, "w", encoding="utf-8") as outfile:
    json.dump(song_database, outfile)
