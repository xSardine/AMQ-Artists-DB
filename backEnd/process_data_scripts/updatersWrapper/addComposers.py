import json
import utils


song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


def add_member_group_links(group_id, group_members, line_up_id):
    # add new group link to new line up members
    for member in group_members:
        print(
            f"adding link '{group_id},{line_up_id}' to {artist_database[member[0]]['names'][0]}"
        )
        artist_database[member[0]]["groups"].append([group_id, line_up_id])
        artist_database[member[0]]["vocalist"] = True


def remove_member_group_links(group_id, line_up_id):
    group = artist_database[group_id]
    for member in group["members"][line_up_id]:
        for j, groupT in enumerate(artist_database[member[0]]["groups"]):
            if groupT[0] == group_id and groupT[1] == line_up_id:
                print(
                    f"removed link '{group_id},{line_up_id}' from {artist_database[member[0]]['names'][0]}"
                )
                artist_database[member[0]]["groups"].pop(j)


def update_new_line_up_in_song_database(group_id, line_up_id, update_songs, mode):
    if mode not in ["edit", "addAll", "addSub"]:
        print("CHOOSE A CORRECT MODE")
        exit(1)

    print("\nUpdated Song:")
    if mode == "addAll":
        for anime in song_database:
            for song in anime["songs"]:
                for artist in song["artist_ids"]:
                    if artist[0] == group_id:
                        print(song["songName"])
                        artist[1] = line_up_id
        print()
        return

    if mode == "addSub":
        for update_song in update_songs:
            flag_song = False
            for anime in song_database:
                for song in anime["songs"]:
                    if utils.check_same_song(song, update_song):
                        flag_artist = False
                        for aid in song["artist_ids"]:
                            if group_id == aid[0]:
                                flag_song = True
                                flag_artist = True
                                aid[1] = line_up_id
                                print(song["songName"])
                        if not flag_artist:
                            print(f"{update_song} FOUND BUT NOT THE RIGHT ARTIST")
            if not flag_song:
                print(f"{update_song} NOT FOUND")

    print()


def remove_line_up(group_id, line_up_id, fall_back_line_up):
    # song - artist links
    print()
    for anime in song_database:
        for song in anime["songs"]:
            for artist in song["artist_ids"]:
                if artist[0] != group_id:
                    continue
                # Update song - artist links for removed line up
                if artist[1] == line_up_id:
                    print(f"{song['songName']} : {artist[1]} → {fall_back_line_up}")
                    artist[1] = fall_back_line_up
                # Update song - artist links for above line ups that got shifted
                elif artist[1] > line_up_id:
                    print(f"{song['songName']} : {artist[1]} → {artist[1]-1}")
                    artist[1] -= 1

    print()
    # Remove artist - group links for line up
    for member in artist_database[group_id]["members"][line_up_id]:
        for i, group in enumerate(artist_database[member[0]]["groups"]):
            if group[0] == group_id and group[1] == line_up_id:
                print(
                    f"Removing artist - group link for {artist_database[member[0]]['names'][0]}, {line_up_id}"
                )
                artist_database[member[0]]["groups"].pop(i)

    print()
    # Update artist - group links for above line-up that got shifted
    for line_up in artist_database[group_id]["members"][line_up_id:]:
        for member in line_up:
            for group in artist_database[member[0]]["groups"]:
                if group[0] == group_id and group[1] > line_up_id:
                    print(
                        f"Updating link for {artist_database[member[0]]['names'][0]}: {group[1]}→{group[1]-1}"
                    )
                    group[1] -= 1

    print()
    # Update line-up for topGroup containing the affected group
    for artist_id in artist_database:
        artist = artist_database[artist_id]
        for line_up in artist["members"]:
            for member in line_up:
                if member[0] != group_id:
                    continue
                # Update group - member links for removed line up
                if member[1] == line_up_id:
                    print(f"{artist['names'][0]} : {member[1]} → {fall_back_line_up}")
                    member[1] = fall_back_line_up
                # Update group - member links for above line ups that got shifted
                elif member[1] > line_up_id:
                    print(f"{artist['names'][0]} : {member[1]} → {member[1]-1}")
                    member[1] -= 1

    artist_database[group_id]["members"].pop(line_up_id)


def process():

    user_input, anime, song = utils.ask_song_id(
        "Please select the song you want to update\n", song_database
    )

    print(f"Anime: {anime['animeExpandName']}")
    print(f"Song: {song['songName']}")
    print(f"Artist: {song['songArtist']}")
    print()

    if song["composer_ids"]:
        print("This song already has a composer\n")
        return

    if song["arranger_ids"]:
        print("This song already has an arranger\n")
        return

    composers = utils.ask_line_up(
        "Please type in the composers you want to add\n",
        song_database,
        artist_database,
        not_exist_ok=True,
    )

    print("\n")

    arrangers = utils.ask_line_up(
        "Please type in the arrangers you want to add\n",
        song_database,
        artist_database,
        not_exist_ok=True,
    )

    song["composer_ids"] = composers
    song["arranger_ids"] = arrangers

    print("\n")

    # recap
    print(
        "Composers: "
        + ", ".join([artist_database[artist[0]]["names"][0] for artist in composers])
    )
    print(
        "Arrangers: "
        + ", ".join([artist_database[artist[0]]["names"][0] for artist in arrangers])
    )
    print()

    validation = utils.ask_validation("Do you want to save the changes? (y/n)\n")

    if not validation:
        print("Changes discarded\n")
        return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile, indent=4)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile, indent=4)


process()
