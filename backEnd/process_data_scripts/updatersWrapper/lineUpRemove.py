import json
import utils

song_database_path = "../../app/data/song_database.json"
artist_database_path = "../../app/data/artist_database.json"

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


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


def process(group_name):

    group_id = utils.get_artist_id(song_database, artist_database, group_name)

    group = artist_database[group_id]

    if len(group["members"]) == 0:
        print("cancelled, it has no line up")
        return

    # skip user input as there's no question needed
    if len(group["members"]) == 1:

        remove_line_up(group_id, 0, -1)

    else:

        print(range(len(group["members"])))

        line_ups = "\n"
        for i, line_up in enumerate(group["members"]):
            line_up = [artist_database[l[0]]["names"][0] for l in line_up]
            line_ups += f"{i}: {', '.join(line_up)}\n"
        line_up_id = utils.ask_integer_input(
            f"Please select the line up you want to remove:{line_ups}",
            range(len(group["members"])),
        )

        line_ups = "\n"
        tmp_line_up = group["members"].copy()
        tmp_line_up.pop(line_up_id)
        for i, line_up in enumerate(tmp_line_up):
            line_up = [artist_database[l[0]]["names"][0] for l in line_up]
            line_ups += f"{i}: {', '.join(line_up)}\n"
        fall_back_line_up = utils.ask_integer_input(
            f"Please select to which line up should the song fall back to:{line_ups}",
            range(len(group["members"]) - 1),
        )

        remove_line_up(group_id, line_up_id, fall_back_line_up)

    validation_message = "Do you validate those changes ?\n"
    validation = utils.ask_validation(validation_message)

    if not validation:
        print("User Cancelled changes")
        return

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)


group_name = "W"

process(group_name)
