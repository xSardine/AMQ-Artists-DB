from functools import partial
import re

ANIME_REGEX_REPLACE_RULES = [
    {"input": "ź", "replace": "[źŹ]"},
    {"input": "ļ", "replace": "[ļĻ]"},
    {"input": "l", "replace": "[l˥ļĻ]"},
    {"input": "z", "replace": "[zźŹ]"},
    {"input": "ou", "replace": "(ou|ō|o)"},
    {"input": "oo", "replace": "(oo|ō|o)"},
    {"input": "oh", "replace": "(oh|ō|o)"},
    {"input": "wo", "replace": "(wo|o)"},
    {"input": "o", "replace": "([oōóòöôøӨΦο]|ou|oo|oh|wo)"},
    {"input": "uu", "replace": "(uu|u|ū)"},
    {"input": "u", "replace": "([uūûúùüǖμ]|uu)"},
    {"input": "aa", "replace": "(aa|a)"},
    {"input": "ae", "replace": "(ae|æ)"},
    {"input": "a", "replace": "([aäά@âàáạåæā∀Λ]|aa)"},
    {"input": "c", "replace": "[cςč℃]"},
    {"input": "e", "replace": "[eəéêёëèæē]"},
    {"input": "'", "replace": "['’ˈ]"},
    {"input": "n", "replace": "[nñ]"},
    {"input": "0", "replace": "[0Ө]"},
    {"input": "2", "replace": "[2²]"},
    {"input": "3", "replace": "[3³]"},
    {"input": "*", "replace": "[*✻＊]"},
    {
        "input": " ",
        "replace": "( ?[²³★☆♥♡\\/\\*✻＊'ˈ∽~〜・·\\.,;:!?@_-⇔→≒=\\+†×±◎Ө♪♣␣∞] ?| )",
    },
    {"input": "i", "replace": "([iíίɪ]|ii)"},
    {"input": "x", "replace": "[x×]"},
    {"input": "b", "replace": "[bßβ]"},
    {"input": "r", "replace": "[rЯ]"},
    {"input": "s", "replace": "[sς]"},
]


def escapeRegExp(str):
    str = re.escape(str)
    str = str.replace("\ ", " ")
    str = str.replace("\*", "*")
    return str


def apply_regex_rules(search):
    for rule in ANIME_REGEX_REPLACE_RULES:
        search = search.replace(rule["input"], rule["replace"])
    return search


def get_regex_search(og_search, partial_match=True, swap_words=True):

    og_search = escapeRegExp(og_search.lower())
    search = apply_regex_rules(og_search)
    search = "^" + search + "$" if not partial_match else ".*" + search + ".*"

    if swap_words:
        alt_search = og_search.split(" ")
        if len(alt_search) == 2:
            alt_search = " ".join([alt_search[1], alt_search[0]])
            alt_search = apply_regex_rules(alt_search)
            alt_search = (
                "^" + alt_search + "$"
                if not partial_match
                else ".*" + alt_search + ".*"
            )
            search = f"({search})|({alt_search})"
    return search


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
        if user_input.isdigit() or user_input[1:].isdigit():
            user_input = int(user_input)
    return user_input


def ask_artist(
    message, song_database, artist_database, not_exist_ok=False, partial_match=False
):

    user_input = input(message)
    artist_id = get_artist_id(
        song_database,
        artist_database,
        user_input,
        not_exist_ok=not_exist_ok,
        partial_match=partial_match,
    )

    return user_input, artist_id


def ask_song_ids():

    song_ids = []

    while True:

        song_id = ask_integer_input(
            "\nPlease, input the song ID you want to update: (-2 to stop)\n",
            range(-2, 50000),
        )

        if song_id == -2:
            break

        if song_id == -1:

            songName = input("Please input the song name exactly as it is:\n")
            songArtist = input("Please input the song artist exactly as it is:\n")

            song_ids.append([songName, songArtist])

        else:

            song_ids.append(int(song_id))

    return song_ids


def ask_line_up(
    message, song_database, artist_database, not_exist_ok=False, partial_match=False
):

    group_members = []
    while True:

        user_input = input(message)

        if user_input == "!":
            break

        member_id = get_artist_id(
            song_database,
            artist_database,
            user_input,
            not_exist_ok=not_exist_ok,
            partial_match=partial_match,
            excluded_ids=[mid[0] for mid in group_members],
        )

        if member_id in [mid[0] for mid in group_members]:
            print("You can't have the same artist twice in the line up !!")
            exit()

        if not artist_database[member_id]["members"]:
            group_members.append([member_id, -1])
            print(f"Adding {[member_id, -1]}")

        elif len(artist_database[member_id]["members"]) == 1:
            group_members.append([member_id, 0])
            print(f"Adding {[member_id, 0]}")

        else:
            print(artist_database[member_id])

            line_ups = "\n"
            for i, line_up in enumerate(artist_database[member_id]["members"]):
                line_up = [artist_database[l[0]]["names"][0] for l in line_up]
                line_ups += f"{i}: {', '.join(line_up)}\n"
            line_up_id = ask_integer_input(
                f"Please select the line up you want to add as a member:{line_ups}",
                range(len(artist_database[member_id]["members"])),
            )
            group_members.append([member_id, line_up_id])
            print(f"Adding {[member_id, line_up_id]}")
        print()

    return group_members


def update_line_up(group, line_up_id, song_database, artist_database):

    group_members = []

    for member in group["members"][line_up_id]:
        user_input = ""
        while user_input not in ["=", "-"]:
            user_input = input(f"{artist_database[member[0]]['names'][0]} ? (=/-)\n")
            if user_input == "=":
                group_members.append(member)
            else:
                print(f"removing {artist_database[member[0]]['names'][0]}")

    line_up = ask_line_up(
        "Select people to add to the line up\n",
        song_database,
        artist_database,
        not_exist_ok=True,
    )
    group_members += line_up
    return group_members


def add_new_artist_to_DB(artist_database, artist, vocalist=True, composing=False):
    new_id = str(int(list(artist_database.keys())[-1]) + 1)
    if new_id not in artist_database:
        artist_database[new_id] = {
            "names": [artist],
            "groups": [],
            "members": [],
            "vocalist": vocalist,
            "composer": composing,
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


def get_recap_artists(song_database, artist_database, ids):

    recap_str = ""
    for id in ids:
        ex_animes = get_example_song_for_artist(song_database, id)
        recap_str += f"{id} {artist_database[id]['names'][0]}> {' | '.join(ex_animes[:min(3, len(ex_animes))])}\n"
    return recap_str


def get_artist_id(
    song_database,
    artist_database,
    artist,
    not_exist_ok=False,
    vocalist=True,
    composing=False,
    partial_match=False,
    exact_match=False,
    excluded_ids=[],
):

    ids = []
    if not exact_match:

        if partial_match:

            artist_regex = get_regex_search(artist)

            for id in artist_database.keys():
                flag = False
                for name in artist_database[id]["names"]:
                    if re.match(artist_regex, name, re.IGNORECASE):
                        flag = True
                if flag:
                    ids.append(id)

        if not partial_match or (ids and len(ids) > 10):
            if partial_match:
                print("Too much results, removing partial match")
            artist_regex = get_regex_search(artist, partial_match=False)
            ids = []
            for id in artist_database.keys():
                flag = False
                for name in artist_database[id]["names"]:
                    if re.match(artist_regex, name, re.IGNORECASE):
                        flag = True
                if flag:
                    ids.append(id)

    else:

        for id in artist_database.keys():
            if artist in artist_database[id]["names"] and id not in ids:
                ids.append(id)

    # if no IDs found
    if not ids:
        if not not_exist_ok:
            print(f"{artist} NOT FOUND, CANCELLED")
            # return -1
        new_id = add_new_artist_to_DB(artist_database, artist, vocalist, composing)
        print(f"COULDN'T FIND {artist}, adding {new_id}")
        return new_id

    if len(ids) > 1:
        for i, id in enumerate(ids):
            if id in excluded_ids:
                ids.pop(i)

    # if more than one ID, ask user to desambiguate
    if len(ids) > 1:

        recap_str = get_recap_artists(song_database, artist_database, ids)

        if not_exist_ok:
            input_message = f"\nMultiple artist found for {artist}, please input the correct ID (-1 if NONE):\n{recap_str}"
            disambiguated_id = ask_integer_input(
                input_message, [int(id) for id in ids] + [-1]
            )
        else:
            input_message = f"\nMultiple artist found for {artist}, please input the correct ID:\n{recap_str}"
            disambiguated_id = ask_integer_input(input_message, [int(id) for id in ids])

        if disambiguated_id == -1:
            new_id = add_new_artist_to_DB(artist_database, artist, vocalist, composing)
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
