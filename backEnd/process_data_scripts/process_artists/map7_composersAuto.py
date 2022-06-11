import json
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


def process_composer_auto_database(song_database, artist_database, composer_database):

    for item in composer_database:
        for update_song in item["songs"]:

            flag_found_song = False

            for source_anime in song_database:
                for source_song in source_anime["songs"]:

                    if type(update_song) == int:

                        if source_song["annSongId"] == update_song:

                            flag_found_song = True

                            composers_list = []
                            for composer in item["artist_list"]:

                                composer_id = get_composer_id(
                                    artist_database, [composer]
                                )
                                artist_database[composer_id]["composer"] = True
                                composers_list.append(composer_id)

                            if item["type"] == "composer":
                                source_song["composer_ids"] = composers_list
                            else:
                                source_song["arranger_ids"] = composers_list

                    else:

                        if (
                            source_anime["annId"] == update_song[0]
                            and source_song["annSongId"] == update_song[1]
                            and source_song["songType"] == update_song[2]
                            and source_song["songNumber"] == update_song[3]
                            and source_song["songName"] == update_song[4]
                            and source_song["songArtist"] == update_song[5]
                        ):
                            flag_found_song = True

                            composers_list = []
                            for composer in item["artist_list"]:

                                composer_id = get_composer_id(
                                    artist_database, [composer]
                                )
                                artist_database[composer_id]["composer"] = True
                                composers_list.append(composer_id)

                            if item["type"] == "composer":
                                source_song["composer_ids"] = composers_list
                            else:
                                source_song["arranger_ids"] = composers_list

            if not flag_found_song:
                print(update_song, "not found")

    return song_database, artist_database


if __name__ == "__main__":

    with open(artist_database_path, encoding="utf-8") as json_file:
        artist_database = json.load(json_file)

    with open(song_database_path, encoding="utf-8") as json_file:
        song_database = json.load(json_file)

    with open("config5_composers_auto.json", encoding="utf-8") as json_file:
        composers_config_auto = json.load(json_file)

    song_database, artist_database = process_composer_auto_database(
        song_database,
        artist_database,
        composers_config_auto,
    )

    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
