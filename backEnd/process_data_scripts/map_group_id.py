import json
import config
from pathlib import Path

"""
Map groups and members
"""

groups_subdivision = config.groups_subdivision

source_input_file = Path("../app/data/artist_mapping.json")
results_output_path = Path("../app/data")


def get_artist_id(artist_ids_mapping, artist):

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]:
            if artist_alt_name == artist:
                return id
    print(artist, "not found... adding it")
    id = len(artist_ids_mapping.keys())
    artist_ids_mapping[id] = [artist]
    return id


with open(source_input_file, encoding="utf-8") as json_file:
    artist_ids_mapping = json.load(json_file)

    print(len(artist_ids_mapping))

    group_mapping = {}
    for group in groups_subdivision.keys():
        group_id = get_artist_id(artist_ids_mapping, group)
        artists_id_list = []
        for artist in groups_subdivision[group]:
            artists_id_list.append(get_artist_id(artist_ids_mapping, artist))
        group_mapping[group_id] = artists_id_list

with open(
    results_output_path / Path("artist_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(artist_ids_mapping, outfile)

with open(
    results_output_path / Path("group_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(group_mapping, outfile)
