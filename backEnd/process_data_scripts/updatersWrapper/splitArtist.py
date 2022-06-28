import json
import utils

"""

update = {"songs": [songId], "composers": ["COMPOSERNAME"], "arrangers": ["ARRANGERNAME"]}

"""


song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


def process(update):

    if not len(update["songs_list"]):
        print("Cancelled, you need to provide a list of songs")
        return

    artist_id = utils.get_artist_id(song_database, artist_database, update["name"])

    new_id = utils.add_new_artist_to_DB(artist_database, update["name"])

    for update_song in update["songs_list"]:
        flag_song = False
        for anime in song_database:
            for song in anime["songs"]:
                if not utils.check_same_song(song, update_song):
                    continue
                for artist in song["artist_ids"]:
                    flag_artist = False
                    if artist_id != artist[0]:
                        continue
                    flag_artist = True
                    flag_song = True
                    print(song["songName"])
                    artist = [new_id, -1]
                if not flag_artist:
                    print(f"{update_song} FOUND, BUT NOT THE RIGHT ARTIST, CANCELLED")
                    exit(1)
        if not flag_song:
            print(f"{update_song} NOT FOUND, CANCELLED")
            exit(1)

    validation_message = f"\nYou will be creating a new {new_id}:{update['name']}\n Do you wish to proceed ?\n"
    validation = utils.ask_validation(validation_message)
    if not validation:
        print("cancelled")
        return

    with open("song_database.json", "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
    with open("artist_database.json", "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)


update = {"name": "NAW NAW", "songs_list": [1]}

process(update)
