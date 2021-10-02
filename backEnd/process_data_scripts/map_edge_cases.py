import json
import config_edge_cases
from pathlib import Path

song_database = Path("../app/data/expand_mapping.json")
artist_database = Path("../app/data/artist_mapping.json")
group_database = Path("../app/data/group_mapping.json")
results_output_path = Path("../app/data/")

results_output_path.mkdir(parents=False, exist_ok=True)

with open(song_database, encoding="utf-8") as json_file:
    song_database = json.load(json_file)

with open(artist_database, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)

with open(group_database, encoding="utf-8") as json_file:
    group_database = json.load(json_file)

same_name_edge_case = config_edge_cases.same_name_edge_case


def get_artist_id(artist_ids_mapping, artist):

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]:
            if artist_alt_name == artist:
                return id
    print(artist, "not found... adding it")
    id = len(artist_ids_mapping.keys())
    artist_ids_mapping[id] = [artist]
    return id


def update_song(song_database, song_id, artist_names, artist_id):

    for anime in song_database:
        for song in anime["songs"]:
            if song["annSongId"] == song_id:
                print("old:", song)
                new_artist_ids = []
                for artist in song["artist_ids"]:
                    flag_to_update = False
                    for artist_name in artist_database[str(artist)]:
                        if artist_name in artist_names:
                            flag_to_update = True
                    if flag_to_update:
                        new_artist_ids.append(artist_id)
                    else:
                        new_artist_ids.append(artist)
                song["artist_ids"] = new_artist_ids
                print("new:", song)
                print()


def add_new_artist(artist_database, new_artist):

    last_id = int(list(artist_database.keys())[-1])
    artist_database[last_id + 1] = new_artist["artist_name"]

    if new_artist["members"] != []:
        group_database[last_id + 1] = []
        for artist in new_artist["members"]:
            group_database[last_id + 1].append(get_artist_id(artist_database, artist))

    return last_id + 1


for edge_case in same_name_edge_case:

    new_id = add_new_artist(artist_database, edge_case["new_artist"])
    for song_id in edge_case["linked_song"]:
        update_song(
            song_database, song_id, edge_case["new_artist"]["artist_name"], new_id
        )


with open(
    results_output_path / Path("artist_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(artist_database, outfile)

with open(
    results_output_path / Path("group_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(group_database, outfile)

with open(
    results_output_path / Path("expand_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(song_database, outfile)
