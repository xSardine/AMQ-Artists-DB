import json
import config2_groups
from pathlib import Path
import numpy as np
from Levenshtein import distance

"""
Map groups and members
"""

groups_subdivision = config2_groups.groups_subdivision

source_input_file = Path("../../public/data/artist_mapping.json")
results_output_path = Path("../../public/data")

song_database = Path("../../public/data/expand_mapping.json")
with open(song_database, encoding="utf-8") as json_file:
    song_database = json.load(json_file)


check_group_new_artists = False


def check_groups_duplicate(group_subdiv_list):

    group_names = [group[0] for group in group_subdiv_list]

    for i, group in enumerate(group_names):
        for group2 in group_names[i + 1 :]:
            if group == group2:
                print(f"WARNING: groups {group} is duplicated")


def get_similar_potential_artist(artist_database, artist):

    for art in artist_database:
        for name in artist_database[art]["names"]:
            if distance(name, artist) < 3:
                print(artist_database[art])
    print()


def get_artist_id(artist_ids_mapping, artist, warning=False):

    # defaulted to new artists
    if type(artist) == list and artist[1]:
        id = len(artist_ids_mapping.keys())
        artist_ids_mapping[id] = {"names": [artist[0]], "groups": [], "members": []}
        return id

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]["names"]:
            if artist_alt_name == artist:
                return id
    if not warning:
        print(artist, "not found... adding it")
        if check_group_new_artists:
            get_similar_potential_artist(artist_ids_mapping, artist)
    else:
        print("\n", "WARNING: GROUP NAME", artist, "DOES NOT EXIST: WARNING", "\n")
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

    check_groups_duplicate(config2_groups.groups_subdivision_list)

    for group in groups_subdivision.keys():
        group_id = get_artist_id(artist_ids_mapping, group, warning=True)
        artists_id_list = []
        for artist in groups_subdivision[group]:
            artists_id_list.append(get_artist_id(artist_ids_mapping, artist))
        artist_ids_mapping[group_id]["members"].append(artists_id_list)
    update_expand_mapping_with_groups(song_database, artist_ids_mapping)

if not check_group_new_artists:
    with open(
        results_output_path / Path("artist_mapping.json"), "w", encoding="utf-8"
    ) as outfile:
        json.dump(artist_ids_mapping, outfile)
