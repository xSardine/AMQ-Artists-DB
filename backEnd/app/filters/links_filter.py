from filters import utils


def search_link(
    song_database, search,
):

    song_list = []
    if "catbox.moe" in search or ".webm" in search or ".mp3" in search:
        for song in song_database:
            if (
                (song["720"] and search in song["720"])
                or (song["480"] and search in song["480"])
                or (song["mp3"] and search in song["mp3"])
            ):
                song_list.append(utils.format_song(song))

    return song_list
