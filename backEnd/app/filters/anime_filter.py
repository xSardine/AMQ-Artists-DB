import re
from filters import utils


def search_anime(
    song_database,
    search,
    ignore_special_character=True,
    partial_match=True,
    case_sensitive=False,
    max_nb_songs=250,
    authorized_types=[],
):

    search = utils.get_regex_search(search, ignore_special_character, partial_match)

    song_list = []
    for anime in song_database:
        if len(song_list) >= max_nb_songs:
            break
        if (case_sensitive and re.match(search, anime["name"])) or (
            not case_sensitive and re.match(search, anime["name"], re.IGNORECASE)
        ):
            for song in anime["songs"]:
                if song["type"] in authorized_types:
                    song_list.append(
                        utils.format_song(anime["annId"], anime["name"], song)
                    )

    return song_list
