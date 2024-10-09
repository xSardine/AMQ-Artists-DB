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
            f"adding link '{group_id},{line_up_id}' to {artist_database[member[0]]['names'][0]['romaji_name']}"
        )
        artist_database[member[0]]["groups"].append([group_id, line_up_id])


def remove_member_group_links(group_id, line_up_id):
    group = artist_database[group_id]
    for member in group["members"][line_up_id]["members"]:
        for j, groupT in enumerate(artist_database[member[0]]["groups"]):
            if groupT[0] == group_id and groupT[1] == line_up_id:
                print(
                    f"removed link '{group_id},{line_up_id}' from {artist_database[member[0]]['names'][0]['romaji_name']}"
                )
                artist_database[member[0]]["groups"].pop(j)


def update_new_line_up_in_song_database(
    group_id, line_up_id, update_songs, mode, line_up_type="vocalists"
):
    if mode not in ["edit", "addAll", "addSub"]:
        print("CHOOSE A CORRECT MODE")
        exit(1)

    print("\nUpdated Song:")
    if mode == "addAll":
        for annId in song_database:
            anime = song_database[annId]
            for song in anime["songs"]:

                if line_up_type == "vocalists":
                    for artist in song["artist_ids"]:
                        if artist[0] == group_id:
                            print(song["romajiSongName"])
                            artist[1] = line_up_id

                elif line_up_type == "composers":
                    for artist in song["composer_ids"]:
                        if artist[0] == group_id:
                            print(song["romajiSongName"])
                            artist[1] = line_up_id

                    for artist in song["arranger_ids"]:
                        if artist[0] == group_id:
                            print(song["romajiSongName"])
                            artist[1] = line_up_id
        print()
        return

    if mode == "addSub":
        for update_song in update_songs:
            flag_song = False
            for annId in song_database:
                anime = song_database[annId]
                for song in anime["songs"]:
                    if utils.check_same_song(song, update_song):
                        flag_artist = False

                        if line_up_type == "vocalists":
                            for aid in song["artist_ids"]:
                                if group_id == aid[0]:
                                    flag_song = True
                                    flag_artist = True
                                    aid[1] = line_up_id
                                    print(song["romajiSongName"])

                        elif line_up_type == "composers":
                            for aid in song["composer_ids"]:
                                if group_id == aid[0]:
                                    flag_song = True
                                    flag_artist = True
                                    aid[1] = line_up_id
                                    print(song["romajiSongName"])

                            for aid in song["arranger_ids"]:
                                if group_id == aid[0]:
                                    flag_song = True
                                    flag_artist = True
                                    aid[1] = line_up_id
                                    print(song["romajiSongName"])

                        if not flag_artist:
                            print(f"{update_song} FOUND BUT NOT THE RIGHT ARTIST")
            if not flag_song:
                print(f"{update_song} NOT FOUND")

    print()


def remove_line_up(group_id, line_up_id, fall_back_line_up):
    # song - artist links
    print()
    for annId in song_database:
        anime = song_database[annId]
        for song in anime["songs"]:
            for artist in song["artist_ids"]:
                if artist[0] != group_id:
                    continue
                # Update song - artist links for removed line up
                if artist[1] == line_up_id:
                    print(
                        f"{song['romajiSongName']} : {artist[1]} → {fall_back_line_up}"
                    )
                    artist[1] = fall_back_line_up
                # Update song - artist links for above line ups that got shifted
                elif artist[1] > line_up_id:
                    print(f"{song['romajiSongName']} : {artist[1]} → {artist[1]-1}")
                    artist[1] -= 1

    print()
    # Remove artist - group links for line up
    for member in artist_database[group_id]["members"][line_up_id]["members"]:
        for i, group in enumerate(artist_database[member[0]]["groups"]):
            if group[0] == group_id and group[1] == line_up_id:
                print(
                    f"Removing artist - group link for {artist_database[member[0]]['names'][0]['romaji_name']}, {line_up_id}"
                )
                artist_database[member[0]]["groups"].pop(i)

    print()
    # Update artist - group links for above line-up that got shifted
    for line_up in artist_database[group_id]["members"][line_up_id:]:
        for member in line_up["members"]:
            for group in artist_database[member[0]]["groups"]:
                if group[0] == group_id and group[1] > line_up_id:
                    print(
                        f"Updating link for {artist_database[member[0]]['names'][0]['romaji_name']}: {group[1]}→{group[1]-1}"
                    )
                    group[1] -= 1

    print()
    # Update line-up for topGroup containing the affected group
    for artist_id in artist_database:
        artist = artist_database[artist_id]
        for line_up in artist["members"]:
            for member in line_up["members"]:
                if member[0] != group_id:
                    continue
                # Update group - member links for removed line up
                if member[1] == line_up_id:
                    print(
                        f"{artist['names'][0]['romaji_name']} : {member[1]} → {fall_back_line_up}"
                    )
                    member[1] = fall_back_line_up
                # Update group - member links for above line ups that got shifted
                elif member[1] > line_up_id:
                    print(
                        f"{artist['names'][0]['romaji_name']} : {member[1]} → {member[1]-1}"
                    )
                    member[1] -= 1

    artist_database[group_id]["members"].pop(line_up_id)


def process():
    user_input, group_id = utils.ask_artist(
        "Please input the group to which you want to add a line up\n",
        song_database,
        artist_database,
    )
    group = artist_database[group_id]

    print()

    if not group["members"]:
        print(
            f"No Line Up found for {group['names'][0]['romaji_name']}, automatically adding to every songs\n"
        )

        group_members = utils.ask_line_up(
            "Please type in the members you want to add\n",
            song_database,
            artist_database,
            not_exist_ok=True,
        )

        if not group_members:
            print("There are no members to add, cancelled")
            return

        group_recap_str1 = f"group {group['names'][0]['romaji_name']}: {' | '.join(utils.get_example_song_for_artist(song_database, group_id)[:min(3, len(utils.get_example_song_for_artist(song_database, group_id)))])}"

        group_recap_str2 = ""
        for member in group_members:
            if member[0] in artist_database:
                group_recap_str2 += f"{artist_database[member[0]]['names'][0]['romaji_name']} {member}> {' | '.join(utils.get_example_song_for_artist(song_database, member[0])[:min(3, len(utils.get_example_song_for_artist(song_database, member[0])))])}\n"
            else:
                group_recap_str2 += f"NEW {member[0]}\n"

        line_up_type = (
            "vocalists"
            if utils.ask_validation("Is it a vocalists group ?\n")
            else "composers"
        )
        group["members"] = [
            {
                "type": line_up_type,
                "members": group_members,
            }
        ]

        if group["type"] == "person":
            group["type"] = "group"

        add_member_group_links(group_id, group_members, 0)

        # change line up for any group containing this group as it is now a group
        for artist in artist_database:
            artist = artist_database[artist]
            for line_up in artist["members"]:
                for member in line_up:
                    if member[0] == group_id:
                        print(
                            f"Swapping to line up 0 in {artist['names'][0]['romaji_name']}"
                        )
                        member[1] = 0

        update_new_line_up_in_song_database(group_id, 0, [], "addAll", line_up_type)

        validation_message = f"You will add the first line-up to every song by the {group_recap_str1}\nThe line up is composed of:\n{group_recap_str2}\nDo you validate this change ?\n"
        validation = utils.ask_validation(validation_message)
        if not validation:
            print("User Cancelled")
            return

    else:
        validation = utils.ask_validation(
            "There are already existing line up, do you want to remove one ?\n"
        )
        if validation:
            # skip user input as there's no question needed
            if len(group["members"]) == 1:
                remove_line_up(group_id, 0, -1)

                if group["type"] == "group":
                    group["type"] = "person"

            else:
                print(range(len(group["members"])))

                line_ups = "\n"
                for i, line_up in enumerate(group["members"]):
                    line_up = [
                        artist_database[l[0]]["names"][0]["romaji_name"]
                        for l in line_up["members"]
                    ]
                    line_ups += f"{i}: {', '.join(line_up)}\n"
                line_up_id = utils.ask_integer_input(
                    f"Please select the line up you want to remove:{line_ups}",
                    range(len(group["members"])),
                )

                line_ups = "\n"
                tmp_line_up = group["members"].copy()
                tmp_line_up.pop(line_up_id)
                for i, line_up in enumerate(tmp_line_up):
                    line_up = [
                        artist_database[l[0]]["names"][0]["romaji_name"]
                        for l in line_up["members"]
                    ]
                    line_ups += f"{i}: {', '.join(line_up)}\n"
                fall_back_line_up = utils.ask_integer_input(
                    f"Please select to which line up should the song fall back to:{line_ups}",
                    range(len(group["members"]) - 1),
                )

                remove_line_up(group_id, line_up_id, fall_back_line_up)

            validation_message = "Do you validate those changes ?\n"
            validation = utils.ask_validation(validation_message)
            if not validation:
                print("USER CANCELLED")
                return

        else:
            line_ups = "\n"
            for i, line_up in enumerate(group["members"]):
                line_up = [
                    artist_database[l[0]]["names"][0]["romaji_name"]
                    for l in line_up["members"]
                ]
                line_ups += f"{i}: {', '.join(line_up)}\n"

            line_up_id = utils.ask_integer_input(
                f"There are already line-ups linked to this group, input the one you want to update or -1 if you want to add a new one:\n{line_ups}",
                range(-1, len(group["members"])),
            )

            if line_up_id != -1:
                print("Updating a line up\n")

                group_members = utils.update_line_up(
                    group,
                    line_up_id,
                    song_database,
                    artist_database,
                )

                if not group_members:
                    print("There are no members to add, cancelled")
                    return

                group_recap_str1 = f"group {group['names'][0]['romaji_name']}: {' | '.join(utils.get_example_song_for_artist(song_database, group_id)[:min(3, len(utils.get_example_song_for_artist(song_database, group_id)))])}"

                group_recap_str2 = ""
                for member in group_members:
                    if member[0] in artist_database:
                        group_recap_str2 += f"{artist_database[member[0]]['names'][0]['romaji_name']} {member}> {' | '.join(utils.get_example_song_for_artist(song_database, member[0])[:min(3, len(utils.get_example_song_for_artist(song_database, member[0])))])}\n"
                    else:
                        group_recap_str2 += f"NEW {member[0]}\n"

                remove_member_group_links(group_id, line_up_id)

                add_member_group_links(group_id, group_members, line_up_id)

                print(
                    "Select the songs you want to update, if already linked: removed if not already linked: added to line up\n"
                )
                linked_songs = utils.ask_song_ids()

                line_up_type = (
                    "vocalists"
                    if utils.ask_validation("Is it a vocalists group ?\n")
                    else "composers"
                )

                group["members"][line_up_id] = {
                    "type": line_up_type,
                    "members": group_members,
                }

                update_new_line_up_in_song_database(
                    group_id, line_up_id, linked_songs, "addSub", line_up_type
                )

                validation_message = f"You will update line-up n°{line_up_id} of the {group_recap_str1}\nThis line up will be composed of:\n{group_recap_str2}\nDo you validate this change ?\n"
                validation = utils.ask_validation(validation_message)
                if not validation:
                    print("USER CANCELLED")
                    return

            else:
                print("Creating a new line up\n")

                group_members = utils.ask_line_up(
                    "Please type in the members you want to add\n",
                    song_database,
                    artist_database,
                    not_exist_ok=True,
                )

                if not group_members:
                    print("There are no members to add, cancelled")
                    return

                group_recap_str1 = f"group {group['names'][0]['romaji_name']}: {' | '.join(utils.get_example_song_for_artist(song_database, group_id)[:min(3, len(utils.get_example_song_for_artist(song_database, group_id)))])}"

                group_recap_str2 = ""
                for member in group_members:
                    if member[0] in artist_database:
                        group_recap_str2 += f"{artist_database[member[0]]['names'][0]['romaji_name']} {member}> {' | '.join(utils.get_example_song_for_artist(song_database, member[0])[:min(3, len(utils.get_example_song_for_artist(song_database, member[0])))])}\n"
                    else:
                        group_recap_str2 += f"NEW {member[0]}\n"

                line_up_id = len(group["members"])

                linked_songs = utils.ask_song_ids()

                if not linked_songs:
                    validation_message = f"There are no songs to link to this line up, are you sure you want to continue ?\n"
                    validation = utils.ask_validation(validation_message)
                    if not validation:
                        print("USER CANCELLED")
                        return

                add_member_group_links(group_id, group_members, line_up_id)

                line_up_type = (
                    "vocalists"
                    if utils.ask_validation("Is it a vocalists group ?\n")
                    else "composers"
                )

                group["members"].append(
                    {
                        "type": line_up_type,
                        "members": group_members,
                    }
                )

                update_new_line_up_in_song_database(
                    group_id, line_up_id, linked_songs, "addSub", line_up_type
                )

                validation_message = f"You will add a new line-up (n°{line_up_id}) to the {group_recap_str1}\non the songs {linked_songs}\nThis line up will be composed of:\n{group_recap_str2}\nDo you validate this change ?\n"
                validation = utils.ask_validation(validation_message)
                if not validation:
                    print("USER CANCELLED")
                    return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile, indent=4)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile, indent=4)


"""
enter the "group", and the "member" of the line up to add/update
if there are not any line up yet, will add automatically to line up 0, and link every song by this artist
if there are line up already, will ask you to either edit existing one or create a new one:
    - edit existing one will swap old line up with new line up, and if linked_songs will also add/remove song linked depending of their current state
    - add a new one will create a new line up and link any song in linked_songs
"""

process()

# remove old groups on update
