import json
import utils


song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


def process():

    user_input, artist_id = utils.ask_artist(
        "Please input the artist you want to split\n",
        song_database,
        artist_database,
        not_exist_ok=False,
    )
    artist = artist_database[artist_id]
    new_id = utils.add_new_artist_to_DB(artist_database, user_input)

    linked_song = utils.ask_song_ids()

    if not len(linked_song):
        print("Cancelled, you need to provide a list of songs")
        return

    print()
    for update_song in linked_song:
        flag_song = False
        for anime in song_database:
            for song in anime["songs"]:
                if not utils.check_same_song(song, update_song):
                    continue
                for i, artist in enumerate(song["artist_ids"]):
                    flag_artist = False
                    if artist_id != artist[0]:
                        continue
                    flag_artist = True
                    flag_song = True
                    print(
                        f"{song['songName']} {song['artist_ids'][i]} → {[new_id, -1]}"
                    )
                    song["artist_ids"][i] = [new_id, -1]
                if not flag_artist:
                    print(f"{update_song} FOUND, BUT NOT THE RIGHT ARTIST")
        if not flag_song:
            print(f"{update_song} NOT FOUND")

    validation_message = f"\nYou will be creating a new {new_id}: {linked_song}\n Do you wish to proceed ?\n"
    validation = utils.ask_validation(validation_message)
    if not validation:
        print("cancelled")
        return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)


process()
