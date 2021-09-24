from filters import utils


def search_link(
    song_database, search,
):

    if "catbox.moe" in search:
        for anime in song_database:
            for song in anime["songs"]:
                if search in song["examples"].values():
                    romaji = anime["romaji"] if "romaji" in anime.keys() else None
                    song = utils.format_song(
                        anime["annId"], anime["name"], romaji, song
                    )
                    return [song]

    return []
