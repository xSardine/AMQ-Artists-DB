def ask_validation(message):

    validation = None
    while validation != "n" and validation != "y":
        validation = input(message)
    if validation == "n":
        return False
    return True


def ask_integer_input(message, allowed_values):

    user_input = None
    while user_input not in allowed_values:
        user_input = input(message)
        if user_input.isdigit() or user_input == "-1":
            user_input = int(user_input)
    return user_input


def add_new_artist_to_DB(artist_database, artist):
    new_id = str(int(list(artist_database.keys())[-1]) + 1)
    if new_id not in artist_database:
        artist_database[new_id] = {
            "names": [artist],
            "groups": [],
            "members": [],
            "vocalist": True,
            "composer": False,
        }
    return new_id


def add_new_composer_to_DB(artist_database, artist):
    new_id = str(int(list(artist_database.keys())[-1]) + 1)
    if new_id not in artist_database:
        artist_database[new_id] = {
            "names": [artist],
            "groups": [],
            "members": [],
            "vocalist": False,
            "composer": True,
        }
    return new_id


def get_example_song_for_artist(song_database, artist_id):

    example_animes = set()
    for anime in song_database:
        for song in anime["songs"]:
            if artist_id in [aid[0] for aid in song["artist_ids"]] + [
                cid[0] for cid in song["composer_ids"]
            ] + [arid[0] for arid in song["arranger_ids"]]:
                example_animes.add(anime["animeExpandName"])
                break
    return list(example_animes)


def get_recap_artists(song_database, ids):

    recap_str = ""
    for id in ids:
        ex_animes = get_example_song_for_artist(song_database, id)
        recap_str += f"{id}> {' | '.join(ex_animes[:min(3, len(ex_animes))])}\n"
    return recap_str


def get_artist_id(song_database, artist_database, artist, not_exist_ok=False):

    ids = []
    for id in artist_database.keys():
        if artist in artist_database[id]["names"]:
            ids.append(id)

    # if no IDs found
    if not ids:
        if not not_exist_ok:
            print(f"{artist} NOT FOUND, CANCELLED")
            exit(0)
        new_id = add_new_artist_to_DB(artist_database, artist)
        print(f"COULDN'T FIND {artist}, adding {new_id}")
        return new_id

    # if more than one ID, ask user to desambiguate
    if len(ids) > 1:

        recap_str = get_recap_artists(song_database, ids)

        if not_exist_ok:
            input_message = f"\nMultiple artist found for {artist}, please input the correct ID (-1 if NONE):\n{recap_str}"
            disambiguated_id = ask_integer_input(
                input_message, [int(id) for id in ids] + [-1]
            )
        else:
            input_message = f"\nMultiple artist found for {artist}, please input the correct ID:\n{recap_str}"
            disambiguated_id = ask_integer_input(input_message, [int(id) for id in ids])

        if disambiguated_id == -1:
            new_id = add_new_artist_to_DB(artist_database, artist)
            print(f"ASKED TO CREATE NEW {artist}, adding {new_id}")
            return new_id

        return str(disambiguated_id)

    # else return found ID
    print(f"Found existing artist for {artist}")
    return ids[0]


def check_same_song(source_song, song):
    if song == source_song["annSongId"] or (
        type(song) == list
        and song[0] == source_song["songName"]
        and song[1] == source_song["songArtist"]
    ):
        return True
    return False
