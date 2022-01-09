from filters import utils


def search_annId(
    song_database,
    annId,
    max_nb_songs=300,
    authorized_types=[],
):

    song_list = []

    # If the search is an ANNID
    if str(annId).isdecimal():
        for song in song_database:
            if len(song_list) >= max_nb_songs:
                break
            if song["annId"] == int(annId) and song["type"] in authorized_types:
                song_list.append(utils.format_song(song))

    return song_list
