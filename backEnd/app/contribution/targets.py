"""Catalog target identities, resolution, and display descriptions."""

import json
from contribution.models import FIELDS


def artist_detail(artist_id, disambiguation):
    return f"Artist #{artist_id}" + (f" · {disambiguation}" if disambiguation else "")


def song_type_label(song_type, song_number):
    if song_type == 3:
        return "IN"
    prefix = {1: "OP", 2: "ED"}.get(song_type)
    return f"{prefix}{song_number}" if prefix else "Unknown"


def describe(kind, record):
    if kind == "anime":
        return {
            "label": record.anime_jp_name or record.anime_en_name,
            "detail": f"{record.anime_type or ''} · {record.anime_vintage or ''}",
            "locator": {"ann_id": record.ann_id},
            "names": [record.anime_jp_name, record.anime_en_name],
        }
    if kind == "artist":
        artist_id, artist = record
        return {
            "label": " / ".join(artist.names),
            "detail": artist_detail(artist_id, artist.disambiguation),
            "locator": {"artist_id": artist_id},
            "names": list(artist.names),
            "type": artist.type,
            "disambiguation": artist.disambiguation,
        }
    return {
        "label": f"{record.romaji_song_name} — {record.romaji_song_artist or ''}",
        "detail": f"{record.anime_jp_name or record.anime_en_name} · {song_type_label(record.song_type, record.song_number)}",
        "anime_label": record.anime_jp_name or record.anime_en_name,
        "song_type": record.song_type,
        "song_number": record.song_number,
        "locator": {
            "ann_song_id": record.ann_song_id,
            "ann_id": record.ann_id,
            "amq_song_id": record.amq_song_id,
        },
        "names": [record.romaji_song_name],
    }


def same_artist(identity, artist):
    return (
        bool(set(identity["names"]).intersection(artist.names))
        and identity["type"] == artist.type
        and identity.get("disambiguation") == artist.disambiguation
    )


def resolve(target, by_ann, by_song, artists):
    locator = json.loads(target["locator_json"])
    kind = target["kind"]
    if kind == "artist":
        artist = artists.get(locator["artist_id"])
        if artist is None:
            raise ValueError("Artist no longer exists.")
        identity = json.loads(target["identity_snapshot_json"])
        if not same_artist(identity, artist):
            raise ValueError("Artist identity changed; original names were not applied.")
        return artist
    rows = (
        by_ann.get(locator["ann_id"], ())
        if kind == "anime"
        else [
            song
            for song in by_song.get(locator["ann_song_id"], ())
            if song.ann_id == locator["ann_id"] and song.amq_song_id == locator["amq_song_id"]
        ]
    )
    if not rows or (kind == "song" and len(rows) != 1):
        raise ValueError("Catalog target is missing or ambiguous.")
    return rows


def field_values(kind, resolved):
    record = resolved if kind == "artist" else resolved[0]
    return {
        field: list(value) if isinstance(value := getattr(record, attribute), tuple) else value
        for field, attribute in FIELDS[kind].items()
    }
