from filters import utils


def search_link(
    song_database, search,
):

    song_list = []
    if "catbox.moe" in search or ".webm" in search or ".mp3" in search:
        for anime in song_database:
            for song in anime["songs"]:
                for song_link in song["examples"].values():
                    if song_link and search in song_link:
                        romaji = anime["romaji"] if "romaji" in anime.keys() else None
                        song_list.append(
                            utils.format_song(
                                anime["annId"], anime["name"], romaji, song
                            )
                        )

    return song_list
