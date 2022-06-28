import json
import utils

song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


def process(update):

    if not update["songs"]:
        print("You need to input songs for which to add the composing team !")
        return

    composers_ids = []
    for composer in update["composers"]:
        line_up_id = -1
        if type(composer) == list:
            line_up_id = composer[1]
            composer = composer[0]
        composer_id = utils.get_artist_id(
            song_database, artist_database, composer, not_exist_ok=True
        )
        composers_ids.append([composer_id, line_up_id])

    arrangers_ids = []
    for arranger in update["arrangers"]:
        line_up_id = -1
        if type(arranger) == list:
            line_up_id = arranger[1]
            arranger = arranger[0]
        arranger_id = utils.get_artist_id(
            song_database, artist_database, arranger, not_exist_ok=True
        )
        arrangers_ids.append([arranger_id, line_up_id])

    for update_song in update["songs"]:
        flag_song = False
        for anime in song_database:
            for song in anime["songs"]:
                if utils.check_same_song(song, update_song):
                    flag_song = True
                    print(song["songName"])
                    if update["composers"]:
                        old_composers = [
                            artist_database[comp[0]]["names"][0]
                            for comp in song["composer_ids"]
                        ]
                        print(f"Swapping composers from {old_composers}")
                        song["composer_ids"] = composers_ids
                    if update["arrangers"]:
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
        f"You will be adding {update['composers']} ({composers_ids}) in the composers field"
        if update["composers"]
        else "You will not be touching the composer"
    )
    arranger_str = (
        f"You will be adding {update['arrangers']} ({arrangers_ids}) in the arrangers field"
        if update["arrangers"]
        else "You will not be touching the arranger"
    )

    validation_message = f"\nThis change will affect the following songs: {update['songs']}\n{composer_str}\n{arranger_str}\nDo you wish to proceed ?\n"
    validation = utils.ask_validation(validation_message)
    if not validation:
        print("User cancelled changes")
        return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)


update = {
    "songs": [1, 2],
    "composers": ["Hiroyuki Sawano", "Composing Genius"],
    "arrangers": ["SausageTime"],
}

process(update)
