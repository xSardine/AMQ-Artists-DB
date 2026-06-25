"""Startup-loaded, in-memory representation of the read-only song catalog."""

import gzip
import hashlib
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from re import Pattern
from typing import Any

from pydantic import TypeAdapter

import sql_calls
import utils
from db_types import *
from schemas import AnnIdLinkedAnimeEntry
from song_filters import SongFilters

# Limit distinct artist IDs returned by name resolution. Broad partial searches
# can otherwise expand into thousands of artists and candidate songs.
MAX_ARTIST_NAME_MATCHES = 50


@dataclass(frozen=True)
class Catalog:
    song_rows: tuple[SongFullRow, ...]
    songs_by_id: dict[int, SongFullRow]
    anime_by_id: AnimeDatabase
    artists_by_id: ArtistDatabase
    artist_name_rows: ArtistNameRows
    songs_by_artist_id: SongIdReverseMap
    songs_by_composer_id: SongIdReverseMap
    songs_by_arranger_id: SongIdReverseMap
    songs_by_ann_id: SongRowsByExternalId
    songs_by_mal_id: SongRowsByExternalId
    songs_by_ann_song_id: SongRowsByExternalId
    songs_by_amq_song_id: SongRowsByExternalId
    artist_autocomplete_values: tuple[str, ...]
    song_name_autocomplete_values: tuple[str, ...]
    annid_linked_ids_json: bytes
    annid_linked_ids_gzip: bytes
    annid_linked_ids_etag: str
    database_totals: DatabaseTotalsPayload

    def resolve_artist_ids(
        self, regex: Pattern[str], match_case: bool = False
    ) -> list[int]:
        """Match cached artist aliases and return up to 50 distinct artist IDs."""
        artist_ids: list[int] = []
        seen_artist_ids: set[int] = set()

        for artist_id, name in self.artist_name_rows:
            if artist_id in seen_artist_ids:
                continue
            if not utils.regex_matches(regex, name, match_case):
                continue

            seen_artist_ids.add(artist_id)
            artist_ids.append(artist_id)
            if len(artist_ids) >= MAX_ARTIST_NAME_MATCHES:
                break

        return artist_ids

    def flatten_credits(self, credits: Credits, bottom: bool = True) -> frozenset[int]:
        """Flatten credited groups into performer IDs."""
        members: list[int] = []
        for artist_id, line_up in credits:
            if line_up == -1:
                members.append(artist_id)
                continue

            if not bottom:
                members.append(artist_id)

            artist = self.artists_by_id.get(str(artist_id))
            if not artist:
                continue
            line_ups = artist["line_ups"]
            if line_up >= len(line_ups):
                continue
            members.extend(self.flatten_credits(line_ups[line_up]["members"], bottom))

        return frozenset(members)

    def song_ids_for_artists(self, artist_ids: list[int]) -> list[int]:
        """Return songs.id values linked to any requested artist ID."""
        return sorted(
            {
                song_id
                for artist_id in set(artist_ids)
                for song_id in self.songs_by_artist_id.get(artist_id, ())
            }
        )

    def song_ids_for_composers(
        self,
        composer_ids: list[int],
        arrangement: bool,
    ) -> list[int]:
        """Return songs.id values linked to composer IDs and optionally arranger IDs."""
        reverse_maps = (
            (self.songs_by_composer_id, self.songs_by_arranger_id)
            if arrangement
            else (self.songs_by_composer_id,)
        )
        song_ids = {
            song_id
            for composer_id in set(composer_ids)
            for reverse_map in reverse_maps
            for song_id in reverse_map.get(composer_id, ())
        }
        return sorted(song_ids)

    def random_songs(
        self,
        limit: int,
        song_filters: SongFilters | None = None,
    ) -> list[SongFullRow]:
        """Choose random cached song rows, optionally after applying song filters."""
        if song_filters is None or song_filters.matches_all():
            candidates = self.song_rows
        else:
            candidates = tuple(song for song in self.song_rows if song_filters.matches_row(song))
        return random.sample(candidates, min(limit, len(candidates)))

    def songs_for_external_ids(
        self,
        external_ids: list[int],
        rows_by_external_id: SongRowsByExternalId,
        song_filters: SongFilters,
    ) -> SongMap:
        """Return unique cached rows for external IDs in stable songs.id order."""
        rows = (
            song
            for external_id in set(external_ids)
            for song in rows_by_external_id.get(external_id, ())
        )
        return {
            song[COL_SONG_ID]: song
            for song in sorted(rows, key=lambda song: song[COL_SONG_ID])
            if song_filters.matches_row(song)
        }

    def season_songs(self, season: str, song_filters: SongFilters) -> SongMap:
        """Return unique cached rows whose anime vintage contains the requested season."""
        return {
            song[COL_SONG_ID]: song
            for song in self.song_rows
            if song[COL_ANIME_VINTAGE]
            and season in song[COL_ANIME_VINTAGE]
            and song_filters.matches_row(song)
        }

    def autocomplete_artists(self, search: str | None, count: int) -> list[str]:
        values = self.artist_autocomplete_values
        if search:
            lowered = search.lower()
            values = tuple(value for value in values if lowered in value.lower())
        return list(values[:count])

    def autocomplete_song_names(self, search: str | None, count: int) -> list[str]:
        values = self.song_name_autocomplete_values
        if search:
            lowered = search.lower()
            values = tuple(value for value in values if lowered in value.lower())
        return list(values[:count])

    def autocomplete_anime_names(
        self,
        song_name: str | None,
        song_artist: str | None,
    ) -> list[str]:
        pairs = dict.fromkeys(
            (song[COL_ANIME_JP_NAME], song[COL_ANIME_EN_NAME])
            for song in self.song_rows
            if (not song_name or song[COL_ROMAJI_SONG_NAME] == song_name)
            and (not song_artist or song[COL_ROMAJI_SONG_ARTIST] == song_artist)
        )
        return sorted((jp_name or en_name for jp_name, en_name in pairs), key=str.lower)


def _freeze_row_map(
    rows: defaultdict[int, list[SongFullRow]],
) -> SongRowsByExternalId:
    return {external_id: tuple(songs) for external_id, songs in rows.items()}


def _freeze_reverse_map(rows: defaultdict[int, list[int]]) -> SongIdReverseMap:
    return {person_id: tuple(song_ids) for person_id, song_ids in rows.items()}


def load_catalog() -> Catalog:
    """Load database source rows once and build the read catalog indexes."""
    song_rows = sql_calls.load_song_rows()
    artists_by_id = sql_calls.load_artist_database()

    songs_by_id: dict[int, SongFullRow] = {}
    anime_by_id: AnimeDatabase = {}
    songs_by_artist: defaultdict[int, list[int]] = defaultdict(list)
    songs_by_composer: defaultdict[int, list[int]] = defaultdict(list)
    songs_by_arranger: defaultdict[int, list[int]] = defaultdict(list)
    songs_by_ann: defaultdict[int, list[SongFullRow]] = defaultdict(list)
    songs_by_mal: defaultdict[int, list[SongFullRow]] = defaultdict(list)
    songs_by_ann_song: defaultdict[int, list[SongFullRow]] = defaultdict(list)
    songs_by_amq_song: defaultdict[int, list[SongFullRow]] = defaultdict(list)
    artist_autocomplete_values: dict[str, None] = {}
    song_name_autocomplete_values: dict[str, None] = {}
    annid_linked_ids: dict[int, dict[str, Any]] = {}

    song_type_counts: Counter[int] = Counter()
    broadcast_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    anime_type_counts: Counter[str] = Counter()
    seasons: set[str] = set()
    anime_ids: set[int] = set()
    hq_count = mq_count = audio_count = 0

    for song in song_rows:
        song_id = song[COL_SONG_ID]
        ann_id = song[COL_ANN_ID]
        songs_by_id[song_id] = song
        anime_ids.add(ann_id)
        songs_by_ann[ann_id].append(song)
        if song[COL_MAL_ID] is not None:
            songs_by_mal[song[COL_MAL_ID]].append(song)
        if song[COL_ANN_SONG_ID] is not None:
            songs_by_ann_song[song[COL_ANN_SONG_ID]].append(song)
        if song[COL_AMQ_SONG_ID] is not None:
            songs_by_amq_song[song[COL_AMQ_SONG_ID]].append(song)

        anime = anime_by_id.setdefault(
            ann_id,
            {
                "animeJPName": song[COL_ANIME_JP_NAME],
                "animeENName": song[COL_ANIME_EN_NAME],
                "animeAltNames": song[COL_ROMAJI_ALT_NAMES],
                "animeVintage": song[COL_ANIME_VINTAGE],
                "animeType": song[COL_ANIME_TYPE],
                "animeCategory": song[COL_ANIME_CATEGORY],
                "songs": [],
            },
        )
        anime["songs"].append(song)

        if ann_id not in annid_linked_ids:
            annid_linked_ids[ann_id] = {
                "animeENName": song[COL_ANIME_EN_NAME],
                "animeJPName": song[COL_ANIME_JP_NAME],
                "animeAltName": (
                    song[COL_ROMAJI_ALT_NAMES].split("\\$")
                    if song[COL_ROMAJI_ALT_NAMES]
                    else []
                ),
                "linked_ids": {
                    "annId": ann_id,
                    "myanimelist": song[COL_MAL_ID],
                    "anidb": song[COL_ANIDB_ID],
                    "anilist": song[COL_ANILIST_ID],
                    "kitsu": song[COL_KITSU_ID],
                },
            }

        for credits, reverse_map in (
            (song[COL_ARTISTS], songs_by_artist),
            (song[COL_COMPOSERS], songs_by_composer),
            (song[COL_ARRANGERS], songs_by_arranger),
        ):
            if credits:
                for person_id in credits.split(","):
                    reverse_map[int(person_id)].append(song_id)

        artist_autocomplete_values.setdefault(song[COL_ROMAJI_SONG_ARTIST], None)
        song_name_autocomplete_values.setdefault(song[COL_ROMAJI_SONG_NAME], None)
        song_type_counts[song[COL_SONG_TYPE]] += 1
        if song[COL_IS_DUB] == 1:
            broadcast_counts["Dub"] += 1
        if song[COL_IS_REBROADCAST] == 1:
            broadcast_counts["Rebroadcast"] += 1
        if song[COL_IS_DUB] == 0 and song[COL_IS_REBROADCAST] == 0:
            broadcast_counts["Normal"] += 1
        if song[COL_SONG_CATEGORY] is not None:
            category_counts[song[COL_SONG_CATEGORY]] += 1
        anime_type_counts[song[COL_ANIME_TYPE] or "No Type"] += 1
        if song[COL_ANIME_VINTAGE] is not None:
            seasons.add(song[COL_ANIME_VINTAGE])
        hq_count += song[COL_HQ] is not None
        mq_count += song[COL_MQ] is not None
        audio_count += song[COL_AUDIO] is not None

    artist_name_rows = tuple(
        (int(artist_id), name)
        for artist_id, artist in artists_by_id.items()
        for name in artist["names"]
    )
    database_totals: DatabaseTotalsPayload = {
        "total_songs": len(song_rows),
        "total_anime": len(anime_ids),
        "total_artists": len(artists_by_id),
        "total_seasons": len(seasons),
        "links_by_type": {"HQ": hq_count, "MQ": mq_count, "audio": audio_count},
        "songs_by_type": {
            "Opening": song_type_counts[1],
            "Ending": song_type_counts[2],
            "Insert": song_type_counts[3],
        },
        "songs_by_broadcast": dict(broadcast_counts),
        "songs_by_category": dict(category_counts),
        "songs_by_anime_type": dict(anime_type_counts),
    }
    linked_ids_adapter = TypeAdapter(dict[int, AnnIdLinkedAnimeEntry])
    validated_linked_ids = linked_ids_adapter.validate_python(annid_linked_ids)
    linked_ids_json = linked_ids_adapter.dump_json(
        validated_linked_ids,
        by_alias=False,
    )
    linked_ids_etag = f'W/"{hashlib.sha256(linked_ids_json).hexdigest()}"'

    return Catalog(
        song_rows=song_rows,
        songs_by_id=songs_by_id,
        anime_by_id=anime_by_id,
        artists_by_id=artists_by_id,
        artist_name_rows=artist_name_rows,
        songs_by_artist_id=_freeze_reverse_map(songs_by_artist),
        songs_by_composer_id=_freeze_reverse_map(songs_by_composer),
        songs_by_arranger_id=_freeze_reverse_map(songs_by_arranger),
        songs_by_ann_id=_freeze_row_map(songs_by_ann),
        songs_by_mal_id=_freeze_row_map(songs_by_mal),
        songs_by_ann_song_id=_freeze_row_map(songs_by_ann_song),
        songs_by_amq_song_id=_freeze_row_map(songs_by_amq_song),
        artist_autocomplete_values=tuple(sorted(artist_autocomplete_values, key=str.lower)),
        song_name_autocomplete_values=tuple(sorted(song_name_autocomplete_values, key=len)),
        annid_linked_ids_json=linked_ids_json,
        annid_linked_ids_gzip=gzip.compress(linked_ids_json, compresslevel=9),
        annid_linked_ids_etag=linked_ids_etag,
        database_totals=database_totals,
    )
