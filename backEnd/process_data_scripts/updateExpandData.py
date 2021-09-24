import json
from pathlib import Path

"""
Update the current database with expand new data.
"""

source_input_file = Path("../data/preprocessed/FusedExpand.json")
source_update_file = Path("../data/source/expand.json")

with open(source_input_file, encoding="utf-8") as json_file:
    source_file = json.load(json_file)

with open(source_update_file, encoding="utf-8") as json_file:
    update_file = json.load(json_file)["questions"]


def is_updated(source_anime, source_song, update_anime, update_song):

    if (
        source_anime["name"] == update_anime["name"]
        and source_song["name"] == update_song["name"]
        and source_song["artist"] == update_song["artist"]
        and source_song["examples"] == update_song["examples"]
    ):
        return False

    return True


def similar_song_exist(source_anime, update_song):

    for song in source_anime["songs"]:
        if song["annSongId"] == -1 and (
            song["name"] == update_song["name"]
            or song["artist"] == update_song["artist"]
        ):
            return True
    return False


modification_counter = 0
addSong_counter = 0

for update_anime in update_file:
    for update_song in update_anime["songs"]:
        flag_song_found = False
        for source_anime in source_file:
            if source_anime["annId"] == update_anime["annId"]:
                for i, source_song in enumerate(source_anime["songs"]):
                    if source_song["annSongId"] == update_song["annSongId"]:
                        flag_song_found = True
                        if is_updated(
                            source_anime, source_song, update_anime, update_song
                        ):
                            """if source_song["artist"] != update_song["artist"]:
                                print(
                                    "WARNING: Artists names were updated!",
                                    source_song["artist"],
                                    "-->",
                                    update_song["artist"],
                                )
                                print()"""
                            modification_counter += 1
                            update_song.pop("versions")
                            source_anime["songs"][i] = update_song

                # if song not found but anime found
                if not flag_song_found:
                    if similar_song_exist(source_anime, update_song):
                        print(
                            "HIGH Warning, probably a repeat:",
                            update_anime["annId"],
                            update_anime["name"],
                            update_song,
                        )
                        print()
                        print()
                    elif -1 in [song["annSongId"] for song in source_anime["songs"]]:
                        print(
                            "LOW WARNING: **might** be a repeat:",
                            update_anime["annId"],
                            update_anime["name"],
                            update_song,
                        )
                        print()
                        print()
                        update_song.pop("versions")
                        source_anime["songs"].append(update_song)
                    else:
                        print(
                            "ADDED:",
                            update_anime["annId"],
                            update_anime["name"],
                            update_song,
                        )
                        print()
                        print()
                        update_song.pop("versions")
                        source_anime["songs"].append(update_song)
                    flag_song_found = True

        # if anime not found
        if not flag_song_found:
            songs = []
            for song in update_anime["songs"]:
                song.pop("versions")
                songs.append(song)
            source_file.append(
                {
                    "annId": update_anime["annId"],
                    "name": update_anime["name"],
                    "songs": songs,
                }
            )


with open("../data/preprocessed/FusedExpand.json", "w", encoding="utf-8") as outfile:
    json.dump(source_file, outfile)
