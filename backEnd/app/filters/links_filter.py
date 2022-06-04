from filters import utils


def search_link(
    song_database,
    search,
):

    song_list = []
    if "catbox.moe" in search or ".webm" in search or ".mp3" in search:
        for song in song_database:
            if (
                (song["HQ"] and search in song["HQ"])
                or (song["MQ"] and search in song["MQ"])
                or (song["audio"] and search in song["audio"])
            ):
                song_list.append(utils.format_song(song))

    return song_list
