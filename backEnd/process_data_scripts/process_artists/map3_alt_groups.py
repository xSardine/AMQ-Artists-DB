import json
import config3_alt_groups
from pathlib import Path

song_database = Path("../../app/data/expand_mapping.json")
artist_database = Path("../../app/data/artist_mapping.json")
results_output_path = Path("../../app/data/")

results_output_path.mkdir(parents=False, exist_ok=True)

with open(song_database, encoding="utf-8") as json_file:
    song_database = json.load(json_file)

with open(artist_database, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)

same_group_different_artists = config3_alt_groups.same_group_different_artists


def get_artist_id(artist_ids_mapping, artist):

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]["names"]:
            if artist_alt_name == artist:
                return id
    print(artist, "not found... adding it")
    id = len(artist_ids_mapping.keys())
    artist_ids_mapping[id] = {"names": [artist], "groups": [], "members": []}
    return id


def update_song(song_database, song_id, group_id, new_set):

    flag_valid = False

    for anime in song_database:
        for song in anime["songs"]:

            if int(group_id) not in [int(artId[0]) for artId in song["artist_ids"]]:
                continue

            if type(linked_song) == int:

                if song["annSongId"] != linked_song:
                    continue

                flag_valid = True
                for artist in song["artist_ids"]:
                    if int(artist[0]) == int(group_id):
                        artist[1] = i + 1

            elif type(linked_song) == str:

                if song["songName"] != linked_song:
                    continue

                flag_valid = True
                for artist in song["artist_ids"]:
                    if int(artist[0]) == int(group_id):
                        artist[1] = i + 1

    if not flag_valid:
        print("\n", "WARNING: Song", song_id, "NOT FOUND: WARNING", "\n")


if __name__ == "__main__":
    for edge_case in same_group_different_artists:
        group_id = get_artist_id(artist_database, edge_case["group"])
        for i, alt_config in enumerate(edge_case["alternate_configs"]):
            id_list = []
            for artist in alt_config["members"]:
                id_list.append(get_artist_id(artist_database, artist))
            artist_database[group_id]["members"].append(id_list)

            for linked_song in alt_config["linked_song"]:
                update_song(song_database, linked_song, group_id, i + 1)

    with open(
        results_output_path / Path("artist_mapping.json"), "w", encoding="utf-8"
    ) as outfile:
        json.dump(artist_database, outfile)

    with open(
        results_output_path / Path("expand_mapping.json"), "w", encoding="utf-8"
    ) as outfile:
        json.dump(song_database, outfile)
