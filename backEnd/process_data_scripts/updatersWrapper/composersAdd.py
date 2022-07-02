import json
import utils

song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


def process():

    linked_song = utils.ask_song_ids()

    if not linked_song:
        print("You need to input songs for which to add the composing team !")
        return

    composers_ids = utils.ask_line_up(
        "Please select the composer line up\n",
        song_database,
        artist_database,
        not_exist_ok=True,
    )

    arrangers_ids = utils.ask_line_up(
        "Please select the arranger line up\n",
        song_database,
        artist_database,
        not_exist_ok=True,
    )

    for update_song in linked_song:
        flag_song = False
        for anime in song_database:
            for song in anime["songs"]:
                if utils.check_same_song(song, update_song):
                    flag_song = True
                    print(song["songName"])
                    if composers_ids:
                        old_composers = [
                            artist_database[comp[0]]["names"][0]
                            for comp in song["composer_ids"]
                        ]
                        print(f"Swapping composers from {old_composers}")
                        song["composer_ids"] = composers_ids
                    if arrangers_ids:
                        old_arrangers = [
                            artist_database[arr[0]]["names"][0]
                            for arr in song["arranger_ids"]
                        ]
                        print(f"Swapping arrangers from {old_arrangers}")
                        song["arranger_ids"] = arrangers_ids
        if not flag_song:
            print(f"{update_song} NOT FOUND, CANCELING")
            exit(1)

    composer_str = (
        f"You will be adding {composers_ids} ({composers_ids}) in the composers field"
        if composers_ids
        else "You will not be touching the composer"
    )
    arranger_str = (
        f"You will be adding {arrangers_ids} ({arrangers_ids}) in the arrangers field"
        if arrangers_ids
        else "You will not be touching the arranger"
    )

    validation_message = f"\nThis change will affect the following songs: {linked_song}\n{composer_str}\n{arranger_str}\nDo you wish to proceed ?\n"
    validation = utils.ask_validation(validation_message)
    if not validation:
        print("User cancelled changes")
        return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)


up = {
    "songs": [1, 2],
    "composers": ["Hiroyuki Sawano", "Composing Genius"],
    "arrangers": ["SausageTime"],
}

process()
