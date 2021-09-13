import re

ANIME_REGEX_REPLACE_RULES = [
    {"input": "ou", "replace": "(ou|ō)"},
    {"input": "oo", "replace": "(oo|ō)"},
    {"input": "o", "replace": "[oōóòöôøΦ]"},
    {"input": "u", "replace": "([uūûúùüǖ]|uu)"},
    {"input": "a", "replace": "[aä@âàáạåæā]"},
    {"input": "c", "replace": "[cč]"},
    {"input": " ", "replace": "( ?[★☆\\/\\*=\\+·♥∽・〜†×♪→␣:;~\\-?,.!@_]+ ?| )"},
    {"input": "e", "replace": "[eéêëèæē]"},
    {"input": "'", "replace": "['’]"},
    {"input": "n", "replace": "[nñ]"},
    {"input": "2", "replace": "[2²]"},
    {"input": "i", "replace": "[ií]"},
    {"input": "3", "replace": "[3³]"},
    {"input": "x", "replace": "[x×]"},
    {"input": "b", "replace": "[bß]"},
]


def escapeRegExp(str):
    str = re.escape(str)
    str = str.replace("\ ", " ")
    return str


def get_regex_search(search, ignore_special_character=True, partial_match=True):
    search = escapeRegExp(search)
    if ignore_special_character:
        for rule in ANIME_REGEX_REPLACE_RULES:
            search = search.replace(rule["input"], rule["replace"])
    return "^" + search + "$" if not partial_match else ".*" + search + ".*"


def format_song(annId, anime_name, song):
    if song["type"] == 1:
        type = "Opening " + str(song["number"])
    elif song["type"] == 2:
        type = "Ending " + str(song["number"])
    else:
        type = "Insert Song"

    songinfo = {
        "annId": annId,
        "Anime": anime_name,
        "Type": type,
        "SongName": song["name"],
        "Artist": song["artist"],
        "sept": song["examples"]["720"] if "720" in song["examples"] else None,
        "quatre": song["examples"]["480"] if "480" in song["examples"] else None,
        "mptrois": song["examples"]["mp3"] if "mp3" in song["examples"] else None,
        "artists": song["artist_ids"],
    }

    return songinfo
