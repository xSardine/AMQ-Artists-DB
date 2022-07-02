import json
import utils

song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


def get_fused_artist(ids):

    all_names = set()
    all_groups = []
    all_line_up = []
    vocalist = False
    composer = False
    for id in ids:
        for name in artist_database[id]["names"]:
            all_names.add(name)
        for group in artist_database[id]["groups"]:
            all_groups.append(group)
        for line_up in artist_database[id]["members"]:
            all_line_up.append(line_up)
        if artist_database[id]["vocalist"]:
            vocalist = True
        if artist_database[id]["composer"]:
            composer = True

    all_names = list(all_names)

    return {
        "names": all_names,
        "groups": all_groups,
        "members": all_line_up,
        "vocalist": vocalist,
        "composer": composer,
    }


def process():

    ids = utils.ask_line_up(
        "Type in the artist line up you want to fuse (first one will be the center)\n",
        song_database,
        artist_database,
    )

    ids = [id[0] for id in ids]

    if len(ids) < 2:
        print("You need two people or more to start this process, cancelled")
        return

    recap_artist = ""
    for artist in ids:
        recap_artist += f"{artist}> {artist_database[artist]['names']} - {artist_database[artist]['groups']} - {artist_database[artist]['members']}\n"

    center_id = ids[0]

    print()
    for anime in song_database:
        for song in anime["songs"]:
            for artist in song["artist_ids"]:
                if artist[0] in ids and artist[0] != center_id:
                    print(f"{song['songName']} {artist} → {[center_id, artist[1]]}")
                    artist[0] = center_id

    artist_database[center_id] = get_fused_artist(ids)

    removed_ids = ids
    removed_ids.pop(ids.index(center_id))

    for id in removed_ids:
        artist_database.pop(id)

    print()
    validation_message = f"You will be removing these artists: {removed_ids}\nID {center_id} is chosen to be the one to stay\nNew artist:\n{artist_database[center_id]['names']}\n{artist_database[center_id]['groups']}\n{artist_database[center_id]['members']}\n{artist_database[center_id]['vocalist']}, {artist_database[center_id]['composer']}\nDo you want to proceed ?\n"
    validation = utils.ask_validation(validation_message)
    if not validation:
        print("User cancelled")
        return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)


process()
