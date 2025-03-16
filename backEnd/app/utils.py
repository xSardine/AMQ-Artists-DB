import re

ANIME_REGEX_REPLACE_RULES = [
    # Ļ can't lower correctly with sqlite lower function hence why next line is needed
    {"input": "ļ", "replace": "[ļĻ]"},
    {"input": "l", "replace": "[l˥ļĻΛ]"},
    # Ź can't lower correctly with sqlite lower function hence why next line is needed
    {"input": "ź", "replace": "[źŹ]"},
    {"input": "z", "replace": "[zźŹ]"},
    {"input": "ou", "replace": "(ou|ō|o)"},
    {"input": "oo", "replace": "(oo|ō|o)"},
    {"input": "oh", "replace": "(oh|ō|o)"},
    {"input": "wo", "replace": "(wo|o)"},
    # Ō can't lower correctly with sqlite lower function hence why next line is needed
    {"input": "ō", "replace": "[Ōō]"},
    {"input": "o", "replace": "([oōŌóòöôøӨΦο]|ou|oo|oh|wo)"},
    {"input": "uu", "replace": "(uu|u|ū)"},
    # Ū can't lower correctly with sqlite lower function hence why next line is needed
    {"input": "ū", "replace": "[ūŪ]"},
    {"input": "u", "replace": "([uūŪûúùüǖμ]|uu)"},
    {"input": "aa", "replace": "(aa|a)"},
    {"input": "ae", "replace": "(ae|æ)"},
    # Λ can't lower correctly with sqlite lower function hence why next line is needed
    {"input": "λ", "replace": "[λΛ]"},
    {"input": "a", "replace": "([aäãά@âàáạåæā∀Λ]|aa)"},
    {"input": "c", "replace": "[cςč℃Ↄ]"},
    # É can't lower correctly with sql lower function
    {"input": "é", "replace": "[éÉ]"},
    {"input": "e", "replace": "[eəéÉêёëèæē]"},
    {"input": "'", "replace": "['’ˈ]"},
    {"input": "n", "replace": "[nñ]"},
    {"input": "0", "replace": "[0Ө]"},
    {"input": "2", "replace": "[2²₂]"},
    {"input": "3", "replace": "[3³]"},
    {"input": "5", "replace": "[5⁵]"},
    {"input": "*", "replace": "[*✻＊✳︎]"},
    {
        "input": " ",
        "replace": "([^\\w]+|_+)",
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


def get_regex_search(og_search, partial_match=True, swap_words=False):
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


def format_song(artist_database, song):

    if song[16] == 1:
        type = "Opening " + str(song[17])
    elif song[16] == 2:
        type = "Ending " + str(song[17])
    else:
        type = "Insert Song"

    artists = []
    if song[23]:

        for artist_id, line_up in zip(song[23].split(","), song[24].split(",")):
            line_up = int(line_up)

            artist = artist_database[str(artist_id)]

            current_artist = {
                "id": artist_id,
                "names": artist["names"],
                "line_up_id": line_up,
            }

            if artist["line_ups"] and len(artist["line_ups"]) >= line_up:
                current_artist["members"] = []
                for member in artist["line_ups"][line_up]["members"]:
                    current_artist["members"].append(
                        {
                            "id": member[0],
                            "names": artist_database[str(member[0])]["names"],
                        }
                    )

            if artist["groups"]:
                current_artist["groups"] = []
                added_group = set()
                for group in artist["groups"]:
                    if group[0] in added_group:
                        continue
                    added_group.add(group[0])
                    current_artist["groups"].append(
                        {
                            "id": group[0],
                            "names": artist_database[str(group[0])]["names"],
                        }
                    )

            artists.append(current_artist)

    composers = []
    if song[27]:
        for composer_id, line_up in zip(song[27].split(","), song[28].split(",")):
            line_up = int(line_up)

            composer = artist_database[str(composer_id)]

            current_composer = {
                "id": composer_id,
                "names": composer["names"],
                "line_up_id": line_up,
            }

            if composer["line_ups"] and len(composer["line_ups"]) >= line_up:
                current_composer["members"] = []
                for member in composer["line_ups"][line_up]["members"]:
                    current_composer["members"].append(
                        {
                            "id": member[0],
                            "names": artist_database[str(member[0])]["names"],
                        }
                    )

            if composer["groups"]:
                current_composer["groups"] = []
                added_group = set()
                for group in composer["groups"]:
                    if group[0] in added_group:
                        continue
                    added_group.add(group[0])
                    current_composer["groups"].append(
                        {
                            "id": group[0],
                            "names": artist_database[str(group[0])]["names"],
                        }
                    )

            composers.append(current_composer)

    arrangers = []
    if song[31]:
        for arranger_id, line_up in zip(song[31].split(","), song[32].split(",")):
            line_up = int(line_up)

            arranger = artist_database[str(arranger_id)]

            current_arranger = {
                "id": arranger_id,
                "names": arranger["names"],
                "line_up_id": line_up,
            }

            if arranger["line_ups"] and len(arranger["line_ups"]) >= line_up:
                current_arranger["members"] = []
                for member in arranger["line_ups"][line_up]["members"]:
                    current_arranger["members"].append(
                        {
                            "id": member[0],
                            "names": artist_database[str(member[0])]["names"],
                        }
                    )

            if arranger["groups"]:
                current_arranger["groups"] = []
                added_group = set()
                for group in arranger["groups"]:
                    if group[0] in added_group:
                        continue
                    added_group.add(group[0])
                    current_arranger["groups"].append(
                        {
                            "id": group[0],
                            "names": artist_database[str(group[0])]["names"],
                        }
                    )

            arrangers.append(current_arranger)

    songinfo = {
        "annId": song[0],
        "linked_ids": {
            "myanimelist": song[1],
            "anidb": song[2],
            "anilist": song[3],
            "kitsu": song[4],
        },
        "animeJPName": song[6] if song[6] else song[7],
        "animeENName": song[7] if song[7] else song[6],
        "animeAltName": song[9].split("\$") if song[9] else song[9],
        "animeVintage": song[10],
        "animeType": song[11],
        "animeCategory": song[12],
        "annSongId": song[14],
        "amqSongId": song[15],
        "songType": type,
        "songCategory": song[18],
        "songName": song[20],
        "songArtist": song[22] if song[22] else "",
        "songComposer": song[26] if song[26] else "",
        "songArranger": song[30] if song[30] else "",
        "songDifficulty": song[33],
        "isDub": song[34],
        "isRebroadcast": song[35],
        "songLength": song[36],
        "HQ": song[37],
        "MQ": song[38],
        "audio": song[39],
        "artists": artists,
        "composers": composers,
        "arrangers": arrangers,
    }

    return songinfo
