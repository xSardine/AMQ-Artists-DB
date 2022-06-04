import re

ANIME_REGEX_REPLACE_RULES = [
    {"input": "ou", "replace": "(ou|ō|o)"},
    {"input": "oo", "replace": "(oo|ō|o)"},
    {"input": "oh", "replace": "(oh|ō|o)"},
    {"input": "wo", "replace": "(wo|o)"},
    {"input": "o", "replace": "([oōóòöôøΦο]|ou|oo|oh|wo)"},
    {"input": "uu", "replace": "(uu|u|ū)"},
    {"input": "u", "replace": "([uūûúùüǖ]|uu)"},
    {"input": "aa", "replace": "(aa|a)"},
    {"input": "a", "replace": "([aä@âàáạåæā∀]|aa)"},
    {"input": "c", "replace": "[cč]"},
    {"input": "e", "replace": "[eéêёëèæē]"},
    {"input": "'", "replace": "['’]"},
    {"input": "n", "replace": "[nñ]"},
    {"input": "2", "replace": "[2²]"},
    {"input": " ", "replace": "( ?[²★☆\\/\\*=\\+·♥'♡∽・±⇔≒〜†×♪→␣:∞;~\\-?,.!@_] ?| )"},
    {"input": "i", "replace": "([iíί]|ii)"},
    {"input": "3", "replace": "[3³]"},
    {"input": "x", "replace": "[x×]"},
    {"input": "b", "replace": "[bßβ]"},
    {"input": "r", "replace": "[rЯ]"},
    {"input": "s", "replace": "[sς]"},
    {"input": "l", "replace": "[l˥]"},
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


def format_song(song):
    if song["songType"] == 1:
        type = "Opening " + str(song["songNumber"])
    elif song["songType"] == 2:
        type = "Ending " + str(song["songNumber"])
    else:
        type = "Insert Song"

    songinfo = {
        "annId": song["annId"],
        "annSongId": song["annSongId"],
        "animeExpandName": song["animeExpandName"],
        "animeENName": song["animeENName"],
        "animeJPName": song["animeJPName"],
        "animeVintage": song["animeVintage"],
        "animeType": song["animeType"],
        "songType": type,
        "songName": song["songName"],
        "songArtist": song["songArtist"],
        "songDifficulty": song["songDifficulty"],
        "HQ": song["HQ"],
        "MQ": song["MQ"],
        "audio": song["audio"],
        "artists": song["artists_ids"],
        "composers": song["composers_ids"],
        "arrangers": song["arrangers_ids"],
    }

    return songinfo
