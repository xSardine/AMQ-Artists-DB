import json
from os import link
from pathlib import Path
import config5_composers


song_database_path = Path("../../app/data/expand_mapping.json")
artist_database_path = Path("../../app/data/artist_mapping.json")


to_remove_composer = config5_composers.to_remove_composer
composer_database = config5_composers.composer_database
fix_exception = config5_composers.fix_exception


def get_composer_id(artist_database, composer_names, warning=False):

    for id in artist_database.keys():
        for artist_alt_name in artist_database[id]["names"]:
            if artist_alt_name == composer_names[0]:
                return id
    if warning:
        print(composer_names[0], "NOT FOUND BE CAREFUL")
    id = len(artist_database.keys())
    artist_database[id] = {
        "names": composer_names,
        "groups": [],
        "members": [],
        "vocalist": False,
        "composer": True,
    }
    return int(id)


def remove_credited_composers(song_database, artist_database, to_remove_composer):

    for composer_name in to_remove_composer:

        flag = False

        composer_id = get_composer_id(artist_database, [composer_name], warning=True)

        artist_database[composer_id]["vocalist"] = False
        artist_database[composer_id]["composer"] = True

        for anime in song_database:
            for song in anime["songs"]:

                for i, c_id in enumerate(song["artist_ids"]):
                    if int(c_id[0]) == int(composer_id):
                        song["artist_ids"].pop(i)
                        flag = True

        if not flag:
            print("composer to remove not found:", composer_name)

    return song_database, artist_database


def process_composer_database(song_database, artist_database, composer_database):

    for item in composer_database:

        composers_list = []
        arranger_list = []
        for composer in item["composers"]:
            composer_id = get_composer_id(artist_database, [composer])
            artist_database[composer_id]["composer"] = True
            composers_list.append(composer_id)
        for arranger in item["arrangers"]:
            arranger_id = get_composer_id(artist_database, [arranger])
            artist_database[composer_id]["composer"] = True
            arranger_list.append(arranger_id)

        if "artists_field_sub" in item:

            for artist in item["artists_field_sub"]:
                flag = False
                for anime in song_database:
                    for song in anime["songs"]:

                        if artist not in song["artist"]:
                            continue

                        flag = True

                        for composer in composers_list:
                            if composer in song["composer_ids"]:
                                continue
                            song["composer_ids"].append(composer)

                        for arranger in arranger_list:
                            if arranger in song["arranger_ids"]:
                                continue
                            song["arranger_ids"].append(arranger)
                if not flag:
                    print("artist field sub not found", artist)

        if "artists_ids" in item:

            for artist in item["artists_ids"]:
                flag = False
                artist_id = get_composer_id(artist_database, [artist], warning=True)
                for anime in song_database:
                    for song in anime["songs"]:

                        if int(artist_id) not in [
                            int(temp[0]) for temp in song["artist_ids"]
                        ]:
                            continue

                        flag = True
                        for composer in composers_list:
                            if composer in song["composer_ids"]:
                                continue
                            song["composer_ids"].append(composer)

                        for arranger in arranger_list:
                            if arranger in song["arranger_ids"]:
                                continue
                            song["arranger_ids"].append(arranger)
                if not flag:
                    print("artist id not found:", artist)

        if "songs" in item:
            for linked_song in item["songs"]:
                flag = False

                for anime in song_database:
                    for song in anime["songs"]:

                        if type(linked_song) == int:

                            if song["annSongId"] != linked_song:
                                continue

                            flag = True
                            for composer in composers_list:
                                if composer in song["composer_ids"]:
                                    continue
                                song["composer_ids"].append(composer)

                            for arranger in arranger_list:
                                if arranger in song["arranger_ids"]:
                                    continue
                                song["arranger_ids"].append(arranger)

                        elif type(linked_song) == str:

                            if song["name"] != linked_song:
                                continue

                            flag = True
                            for composer in composers_list:
                                if composer in song["composer_ids"]:
                                    continue
                                song["composer_ids"].append(composer)

                            for arranger in arranger_list:
                                if arranger in song["arranger_ids"]:
                                    continue
                                song["arranger_ids"].append(arranger)

                        elif type(linked_song) == list:

                            if (
                                song["name"] != linked_song[0]
                                or song["artist"] != linked_song[1]
                            ):
                                continue

                            flag = True
                            for composer in composers_list:
                                if composer in song["composer_ids"]:
                                    continue
                                song["composer_ids"].append(composer)

                            for arranger in arranger_list:
                                if arranger in song["arranger_ids"]:
                                    continue
                                song["arranger_ids"].append(arranger)
                if not flag:
                    print("song not found:", linked_song)

    return song_database, artist_database


def process_fix_exception(song_database, artist_database, fix_exception):

    for item in fix_exception:

        composers_list = []
        arranger_list = []
        for composer in item["composers"]:
            composer_id = get_composer_id(artist_database, [composer])
            artist_database[composer_id]["composer"] = True
            composers_list.append(composer_id)
        for arranger in item["arrangers"]:
            arranger_id = get_composer_id(artist_database, [arranger])
            artist_database[composer_id]["composer"] = True
            arranger_list.append(arranger_id)

        if "artists_field_sub" in item:

            for artist in item["artists_field_sub"]:
                flag = False
                for anime in song_database:
                    for song in anime["songs"]:

                        if artist not in song["artist"]:
                            continue

                        flag = True

                        song["composer_ids"] = []
                        song["arranger_ids"] = []
                        for composer in composers_list:
                            if composer in song["composer_ids"]:
                                continue
                            song["composer_ids"].append(composer)

                        for arranger in arranger_list:
                            if arranger in song["arranger_ids"]:
                                continue
                            song["arranger_ids"].append(arranger)
                if not flag:
                    print("artist field sub not found", artist)

        if "artists_ids" in item:

            for artist in item["artists_ids"]:
                flag = False
                artist_id = get_composer_id(artist_database, [artist], warning=True)
                for anime in song_database:
                    for song in anime["songs"]:

                        if int(artist_id) not in [
                            int(temp[0]) for temp in song["artist_ids"]
                        ]:
                            continue

                        song["composer_ids"] = []
                        song["arranger_ids"] = []
                        flag = True
                        for composer in composers_list:
                            if composer in song["composer_ids"]:
                                continue
                            song["composer_ids"].append(composer)

                        for arranger in arranger_list:
                            if arranger in song["arranger_ids"]:
                                continue
                            song["arranger_ids"].append(arranger)
                if not flag:
                    print("artist id not found:", artist)

        if "songs" in item:
            for linked_song in item["songs"]:
                flag = False

                for anime in song_database:
                    for song in anime["songs"]:

                        if type(linked_song) == int:

                            if song["annSongId"] != linked_song:
                                continue

                            flag = True
                            song["composer_ids"] = []
                            song["arranger_ids"] = []
                            for composer in composers_list:
                                if composer in song["composer_ids"]:
                                    continue
                                song["composer_ids"].append(composer)

                            for arranger in arranger_list:
                                if arranger in song["arranger_ids"]:
                                    continue
                                song["arranger_ids"].append(arranger)

                        elif type(linked_song) == str:

                            if song["name"] != linked_song:
                                continue

                            song["composer_ids"] = []
                            song["arranger_ids"] = []
                            flag = True
                            for composer in composers_list:
                                if composer in song["composer_ids"]:
                                    continue
                                song["composer_ids"].append(composer)

                            for arranger in arranger_list:
                                if arranger in song["arranger_ids"]:
                                    continue
                                song["arranger_ids"].append(arranger)

                        elif type(linked_song) == list:

                            if (
                                song["name"] != linked_song[0]
                                or song["artist"] != linked_song[1]
                            ):
                                continue

                            song["composer_ids"] = []
                            song["arranger_ids"] = []
                            flag = True
                            for composer in composers_list:
                                if composer in song["composer_ids"]:
                                    continue
                                song["composer_ids"].append(composer)

                            for arranger in arranger_list:
                                if arranger in song["arranger_ids"]:
                                    continue
                                song["arranger_ids"].append(arranger)
                if not flag:
                    print("song not found:", linked_song)

    return song_database, artist_database


if __name__ == "__main__":

    with open(artist_database_path, encoding="utf-8") as json_file:
        artist_database = json.load(json_file)

    with open(song_database_path, encoding="utf-8") as json_file:
        song_database = json.load(json_file)

    for anime in song_database:
        for song in anime["songs"]:

            if "composer_ids" not in song:
                song["composer_ids"] = []
            if "arranger_ids" not in song:
                song["arranger_ids"] = []

    song_database, artist_database = process_composer_database(
        song_database, artist_database, composer_database
    )

    song_database, artist_database = remove_credited_composers(
        song_database, artist_database, to_remove_composer
    )

    song_database, artist_database = process_fix_exception(
        song_database, artist_database, fix_exception
    )

    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
