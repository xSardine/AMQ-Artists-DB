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

source_input_file = Path("../data/preprocessed/FusedExpand.json")
results_output_path = Path("../app/data/")

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
        for artist_alt_name in artist_ids_mapping[id]:
            if artist_alt_name == artist:
                return id
    return len(artist_ids_mapping.keys())


def add_new_artist_to_DB(artist_ids_mapping, artist, id):

    flag_done = False
    for alt_names in alternative_names:
        if artist in alt_names:
            flag_done = True
            artist_ids_mapping[id] = alt_names
    if not flag_done:
        artist_ids_mapping[id] = []
        artist_ids_mapping[id].append(artist)
    return artist_ids_mapping


with open(source_input_file, encoding="utf-8") as json_file:
    data = json.load(json_file)

    counter = 0
    for anime in data:
        counter += len(anime["songs"])
    print("There is", counter, "songs in", len(data), "animes in the database")

    artist_ids_mapping = {}
    for anime in data:
        for song in anime["songs"]:
            id_list = []
            for artist in split_artist(song["artist"]):
                id = get_artist_id(artist_ids_mapping, artist)
                id_list.append(id)
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
