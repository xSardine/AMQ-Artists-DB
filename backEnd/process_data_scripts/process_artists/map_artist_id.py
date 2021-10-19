import json
import re
import config_exceptions
from pathlib import Path

"""
Map songs and artists
"""

splitters = config_exceptions.splitters
secondary_splitters = config_exceptions.secondary_splitters
splitting_exception = config_exceptions.splitting_exception
alternative_names = config_exceptions.alternative_names

source_input_file = Path("../../data/preprocessed/FusedExpand.json")
results_output_path = Path("../../app/data/")

results_output_path.mkdir(parents=False, exist_ok=True)


def split_artist(artist):

    if artist in splitting_exception.keys():
        return splitting_exception[artist]

    artist_list = re.split(splitters, artist)

    new_list = []
    for art in artist_list:
        if art in splitting_exception.keys():
            [new_list.append(new_artist) for new_artist in splitting_exception[art]]
        else:
            [
                new_list.append(new_artist)
                for new_artist in re.split(secondary_splitters, art)
            ]

    return new_list


def get_artist_id(artist_ids_mapping, artist):

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]["names"]:
            if artist_alt_name == artist:
                return id
    return len(artist_ids_mapping.keys())


def add_new_artist_to_DB(artist_ids_mapping, artist, id):

    flag_done = False
    for alt_names in alternative_names:
        if artist in alt_names:
            flag_done = True
            artist_ids_mapping[id] = {"names": alt_names, "groups": [], "members": []}
    if not flag_done:
        artist_ids_mapping[id] = {"names": [artist], "groups": [], "members": []}
    return artist_ids_mapping


def check_validity(source_input_file, splitting_exception, alternative_names):

    for exception in splitting_exception:
        flag_valid = False
        flag_maybe_valid = False
        for anime in source_input_file:
            for song in anime["songs"]:
                if song["artist"] == exception:
                    flag_valid = True
                elif exception in song["artist"]:
                    flag_maybe_valid = True
        if not flag_valid:
            if flag_maybe_valid:
                print("Split Exception", exception, "MIGHT NOT BE VALID")
            else:
                print(
                    "WARNING: Split Exception",
                    exception,
                    "IS NOT A VALID EXCEPTION: WARNING",
                )

    print("\n\n\n\n")
    for exception in alternative_names:
        for name in exception:
            flag_valid = False
            flag_maybe_valid = False
            for anime in source_input_file:
                for song in anime["songs"]:
                    if song["artist"] == name:
                        flag_valid = True
                    elif name in song["artist"]:
                        flag_maybe_valid = True
            if not flag_valid:
                if flag_maybe_valid:
                    if len(name) < 6:
                        print("Alt Name", name, "MIGHT NOT BE VALID")
                else:
                    print(
                        "WARNING: Alt Name", name, "IS NOT an Alt Name: WARNING",
                    )
    print("done checking")


with open(source_input_file, encoding="utf-8") as json_file:
    data = json.load(json_file)

    counter = 0
    for anime in data:
        counter += len(anime["songs"])
    print("There is", counter, "songs in", len(data), "animes in the database")

    check_validity(data, splitting_exception, alternative_names)

    artist_ids_mapping = {}
    for anime in data:
        for song in anime["songs"]:
            id_list = []
            for artist in split_artist(song["artist"]):
                id = get_artist_id(artist_ids_mapping, artist)
                id_list.append([id, -1])
                if id not in artist_ids_mapping.keys():
                    add_new_artist_to_DB(artist_ids_mapping, artist, id)
            song["artist_ids"] = id_list

with open(
    results_output_path / Path("artist_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(artist_ids_mapping, outfile)

with open(
    results_output_path / Path("expand_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(data, outfile)
