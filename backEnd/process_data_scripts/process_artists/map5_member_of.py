import json
from pathlib import Path

if __name__ == "__main__":
    artist_database_path = Path("../../app/data/artist_mapping.json")

    with open(artist_database_path, encoding="utf-8") as json_file:
        artist_database = json.load(json_file)

    for group in artist_database:
        if len(artist_database[group]["members"]) > 0:
            for i, members_config in enumerate(artist_database[group]["members"]):
                for member in members_config:
                    artist_database[str(member)]["groups"].append([group, i])

    for artist in artist_database:
        artist_database[artist]["vocalist"] = True
        artist_database[artist]["composer"] = False

    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)
