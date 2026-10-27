"""Build song responses and bulk catalog payloads using the public field names."""

from collections.abc import Iterable
from typing import Any

from catalog.models import ArtistDatabase, ArtistEntry, Catalog, Credits, Song

FormattedSong = dict[str, Any]


def _names_for_artist(artist_database: ArtistDatabase, artist_id: int) -> list[str]:
    """Return an artist's names, falling back to the artist ID when unavailable."""
    artist = artist_database.get(artist_id)
    if not artist:
        return [str(artist_id)]
    return list(artist.names) or [str(artist_id)]


def _member_count(artist: ArtistEntry, line_up: int) -> int:
    """How many direct members to report for a group credit."""
    line_ups = artist.line_ups
    if 0 <= line_up < len(line_ups):
        return len(line_ups[line_up].members)
    return len({member_id for lineup in line_ups for member_id, _ in lineup.members})


def _format_credit_entry(
    artist_database: ArtistDatabase, person_id: int, line_up: int
) -> dict[str, Any]:
    """Build one Artist-shaped credit dict (vocalist, composer, or arranger)."""
    artist = artist_database.get(person_id)
    if artist is None:
        return {
            "id": person_id,
            "names": _names_for_artist(artist_database, person_id),
            "line_up_id": line_up,
        }

    entry = {
        "id": person_id,
        "names": list(artist.names) or [str(person_id)],
        "line_up_id": line_up,
        "type": artist.type,
    }
    if artist.type != "person":
        entry["member_count"] = _member_count(artist, line_up)

    # Expand group line-up members when line_up_id is a real index (not -1).
    line_ups = artist.line_ups
    if line_up >= 0 and line_up < len(line_ups):
        entry["members"] = [
            {"id": member[0], "names": _names_for_artist(artist_database, member[0])}
            for member in line_ups[line_up].members
        ]

    groups = artist.groups
    if groups:
        entry["groups"] = []
        added_group = set()
        for group_id, _ in groups:
            # Same group can appear on multiple line-ups; only emit once per group id.
            if group_id in added_group:
                continue
            added_group.add(group_id)
            entry["groups"].append(
                {"id": group_id, "names": _names_for_artist(artist_database, group_id)}
            )

    return entry


def _format_credits(artists: ArtistDatabase, credits: Credits) -> list[dict[str, Any]]:
    return [_format_credit_entry(artists, artist_id, lineup) for artist_id, lineup in credits]


def format_song(artist_database: ArtistDatabase, song: Song) -> FormattedSong:
    """Present a normalized song appearance using the existing public API fields."""
    if song.song_type == 1:
        song_type = "Opening " + str(song.song_number)
    elif song.song_type == 2:
        song_type = "Ending " + str(song.song_number)
    else:
        song_type = "Insert Song"

    songinfo: FormattedSong = {
        "annId": song.ann_id,
        "linked_ids": {
            "myanimelist": song.mal_id,
            "anidb": song.anidb_id,
            "anilist": song.anilist_id,
            "kitsu": song.kitsu_id,
        },
        "animeJPName": song.anime_jp_name or song.anime_en_name,
        "animeENName": song.anime_en_name or song.anime_jp_name,
        "animeAltName": list(song.romaji_alt_names) if song.romaji_alt_names else [],
        "animeVintage": song.anime_vintage,
        "animeType": song.anime_type,
        "animeCategory": song.anime_category,
        "annSongId": song.ann_song_id,
        "amqSongId": song.amq_song_id,
        "songType": song_type,
        "songCategory": song.song_category,
        "songName": song.romaji_song_name,
        "songArtist": song.romaji_song_artist or "",
        "songComposer": song.romaji_song_composer or "",
        "songArranger": song.romaji_song_arranger or "",
        "songDifficulty": song.song_difficulty,
        "isDub": song.is_dub,
        "isRebroadcast": song.is_rebroadcast,
        "songLength": song.song_length,
        "HQ": song.hq,
        "MQ": song.mq,
        "audio": song.audio,
        "artists": _format_credits(artist_database, song.artists),
        "composers": _format_credits(artist_database, song.composers),
        "arrangers": _format_credits(artist_database, song.arrangers),
    }

    return songinfo


def format_songs(catalog: Catalog, songs: Iterable[Song]) -> list[FormattedSong]:
    return [format_song(catalog.artists_by_id, song) for song in songs]


def format_catalog_dump(catalog: Catalog) -> dict[str, Any]:
    """Format anime, songs, and artists with raw credit IDs for the bulk export."""
    song_rows = catalog.song_rows
    artists_by_id = catalog.artists_by_id
    genres_by_ann_id = catalog.genres_by_ann_id
    tags_by_ann_id = catalog.tags_by_ann_id
    anime: dict[str, dict[str, Any]] = {}
    songs: list[dict[str, Any]] = []
    for song in song_rows:
        ann_id = song.ann_id
        ann_key = str(ann_id)
        if ann_key not in anime:
            alt_names = song.romaji_alt_names
            anime[ann_key] = {
                "animeJPName": song.anime_jp_name,
                "animeENName": song.anime_en_name,
                "animeAltName": list(alt_names) if alt_names else [],
                "animeVintage": song.anime_vintage,
                "animeType": song.anime_type,
                "animeCategory": song.anime_category,
                "linked_ids": {
                    "myanimelist": song.mal_id,
                    "anidb": song.anidb_id,
                    "anilist": song.anilist_id,
                    "kitsu": song.kitsu_id,
                },
                "genres": sorted(genres_by_ann_id.get(ann_id, ())),
                "tags": sorted(tags_by_ann_id.get(ann_id, ())),
            }
        songs.append(
            {
                "annId": ann_id,
                "annSongId": song.ann_song_id,
                "amqSongId": song.amq_song_id,
                "songType": song.song_type,
                "songNumber": song.song_number,
                "songCategory": song.song_category,
                "songName": song.romaji_song_name,
                "songArtist": song.romaji_song_artist or "",
                "songComposer": song.romaji_song_composer or "",
                "songArranger": song.romaji_song_arranger or "",
                "songDifficulty": song.song_difficulty,
                "isDub": song.is_dub,
                "isRebroadcast": song.is_rebroadcast,
                "songLength": song.song_length,
                "HQ": song.hq,
                "MQ": song.mq,
                "audio": song.audio,
                "artists": song.artists,
                "composers": song.composers,
                "arrangers": song.arrangers,
            }
        )

    artists: dict[int, dict[str, Any]] = {}
    for artist_id, artist in artists_by_id.items():
        artists[artist_id] = {
            "names": artist.names,
            "type": artist.type,
            "disambiguation": artist.disambiguation,
            "groups": [[group_id, line_up] for group_id, line_up in artist.groups],
            "line_ups": [
                {
                    "line_up_type": line_up.line_up_type,
                    "members": [
                        [member_id, member_line_up] for member_id, member_line_up in line_up.members
                    ],
                }
                for line_up in artist.line_ups
            ],
        }
    return {"anime": anime, "artists": artists, "songs": songs}


def format_annid_linked_ids(catalog: Catalog) -> dict[int, dict[str, Any]]:
    """Format the first appearance of each anime for the linked-ID endpoint."""
    song_rows = catalog.song_rows
    annid_linked_ids: dict[int, dict[str, Any]] = {}
    for song in song_rows:
        ann_id = song.ann_id
        if ann_id not in annid_linked_ids:
            annid_linked_ids[ann_id] = {
                "animeENName": song.anime_en_name,
                "animeJPName": song.anime_jp_name,
                "animeAltName": (list(song.romaji_alt_names) if song.romaji_alt_names else []),
                "linked_ids": {
                    "annId": ann_id,
                    "myanimelist": song.mal_id,
                    "anidb": song.anidb_id,
                    "anilist": song.anilist_id,
                    "kitsu": song.kitsu_id,
                },
            }
    return annid_linked_ids
