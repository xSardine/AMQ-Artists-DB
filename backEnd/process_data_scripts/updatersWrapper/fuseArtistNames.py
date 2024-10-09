import json
import utils

song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


def get_fused_artist(ids):
    all_names = []
    all_groups = []
    all_line_up = []
    disambiguation = None
    type = None
    for id in ids:
        for name in artist_database[id]["names"]:
            all_names.append(name)
        for group in artist_database[id]["groups"]:
            all_groups.append(group)
        for line_up in artist_database[id]["members"]:
            all_line_up.append(line_up)
        if artist_database[id]["disambiguation"]:
            disambiguation = artist_database[id]["disambiguation"]
        if not type:
            type = artist_database[id]["type"]
        elif type != artist_database[id]["type"]:
            print("/!\\ Warning : Ambiguous types")

    all_names = list(all_names)

    return {
        "names": all_names,
        "disambiguation": disambiguation,
        "type": type,
        "members": all_line_up,
        "groups": all_groups,
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
    removed_ids = ids
    removed_ids.pop(ids.index(center_id))

    print()

    # Updating the center_id with the new fused artist
    artist_database[center_id] = get_fused_artist([center_id] + ids)

    # Updating link in song_database for artist, composers and arrangers of deleted artists
    line_up_id = -1
    if artist_database[center_id]["members"]:
        line_up_id = 0
    for annId in song_database:
        anime = song_database[annId]
        for song in anime["songs"]:
            for artist in song["artist_ids"]:
                if artist[0] in removed_ids:
                    print(
                        f"Artist {song['romajiSongName']} {artist} → {[center_id, line_up_id]}"
                    )
                    artist[0] = center_id
                    artist[1] = line_up_id
            for composer in song["composer_ids"]:
                if composer[0] in removed_ids:
                    print(
                        f"Composer {song['romajiSongName']} {composer} → {[center_id, line_up_id]}"
                    )
                    composer[0] = center_id
                    composer[1] = line_up_id
            for arranger in song["arranger_ids"]:
                if arranger[0] in removed_ids:
                    print(
                        f"Arranger {song['romajiSongName']} {arranger} → {[center_id, line_up_id]}"
                    )
                    arranger[0] = center_id
                    arranger[1] = line_up_id

    # Updating every artist that has a deleted artist as a member or a group to now link to center_id
    for id in removed_ids:
        for artist_id in artist_database:
            if artist_id == center_id:
                continue
            artist = artist_database[artist_id]
            for line_up in artist["members"]:
                for member in line_up:
                    if member[0] in removed_ids:
                        print(
                            f"{artist['names'][0]} Member: {member[0]} {member[1]} → {[center_id, line_up_id]}"
                        )
                        member[0] = center_id
                        member[1] = line_up_id
            for group in artist["groups"]:
                if group[0] in removed_ids:
                    print(
                        f"{artist['names'][0]} Group: {group[0]} {group[1]} → {[center_id, group[1]]}"
                    )
                    group[0] = center_id
        artist_database.pop(id)

    print()
    validation_message = f"You will be removing these artists: {removed_ids}\nID {center_id} is chosen to be the one to stay\nNew artist:\n{artist_database[center_id]['names']}\n{artist_database[center_id]['groups']}\n{artist_database[center_id]['members']}\n{artist_database[center_id]['disambiguation']}, {artist_database[center_id]['type']}\nDo you want to proceed ?\n"
    validation = utils.ask_validation(validation_message)
    if not validation:
        print("User cancelled")
        return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile, indent=4)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile, indent=4)


process()

# TODO fusing groups not working
