import json
import config_exceptions
from pathlib import Path

"""
Map groups and members
"""

groups_subdivision = config_exceptions.groups_subdivision

source_input_file = Path("../../app/data/artist_mapping.json")
results_output_path = Path("../../app/data")

song_database = Path("../../app/data/expand_mapping.json")
with open(song_database, encoding="utf-8") as json_file:
    song_database = json.load(json_file)


def get_artist_id(artist_ids_mapping, artist):

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]["names"]:
            if artist_alt_name == artist:
                return id
    print(artist, "not found... adding it")
    id = len(artist_ids_mapping.keys())
    artist_ids_mapping[id] = {"names": [artist], "groups": [], "members": []}
    return id


def update_expand_mapping_with_groups(song_database, artist_ids_mapping):

    for anime in song_database:
        for song in anime["songs"]:
            for artist in song["artist_ids"]:
                if len(artist_ids_mapping[str(artist[0])]["members"]) > 0:
                    artist[1] = 0

    with open(
        results_output_path / Path("expand_mapping.json"), "w", encoding="utf-8"
    ) as outfile:
        json.dump(song_database, outfile)


with open(source_input_file, encoding="utf-8") as json_file:
    artist_ids_mapping = json.load(json_file)

    print(len(artist_ids_mapping))

    for group in groups_subdivision.keys():
        group_id = get_artist_id(artist_ids_mapping, group)
        artists_id_list = []
        for artist in groups_subdivision[group]:
            artists_id_list.append(get_artist_id(artist_ids_mapping, artist))
        artist_ids_mapping[group_id]["members"].append(artists_id_list)
    update_expand_mapping_with_groups(song_database, artist_ids_mapping)

with open(
    results_output_path / Path("artist_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(artist_ids_mapping, outfile)
