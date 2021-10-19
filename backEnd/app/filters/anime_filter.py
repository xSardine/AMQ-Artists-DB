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

    # If the search is an ANNID
    if str(search).isdecimal() and int(search) in [
        anime["annId"] for anime in song_database
    ]:

        song_list = []
        for anime in song_database:
            if len(song_list) >= max_nb_songs:
                break
            if anime["annId"] == int(search):
                for song in anime["songs"]:
                    if song["type"] in authorized_types:
                        romaji = anime["romaji"] if "romaji" in anime.keys() else None
                        song_list.append(
                            utils.format_song(
                                anime["annId"], anime["name"], romaji, song
                            )
                        )
        return song_list

    # If not
    search = utils.get_regex_search(search, ignore_special_character, partial_match)

    song_list = []
    for anime in song_database:
        if len(song_list) >= max_nb_songs:
            break
        anime_romaji = anime["romaji"] if "romaji" in anime.keys() else None

        if (
            case_sensitive
            and (re.match(search, anime["name"]) or re.match(search, anime_romaji))
        ) or (
            not case_sensitive
            and (
                re.match(search, anime["name"], re.IGNORECASE)
                or (anime_romaji and re.match(search, anime_romaji, re.IGNORECASE))
            )
        ):
            for song in anime["songs"]:
                if song["type"] in authorized_types:
                    song_list.append(
                        utils.format_song(
                            anime["annId"], anime["name"], anime_romaji, song
                        )
                    )

    return song_list
