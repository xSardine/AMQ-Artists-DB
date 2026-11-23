"""Compute aggregate counts and missing-data statistics from the catalog."""

from collections import Counter
from typing import TypedDict

from catalog.classification import normalize_anime_type, normalize_song_category, season_index
from catalog.credit_statistics import ArtistCreditStatistics, build_artist_credit_statistics
from catalog.models import Catalog
from catalog.song_statistics import SongAnalysis, build_song_analysis


class DatabaseStatsMissingData(TypedDict):
    songs_without_difficulty: int
    songs_without_length: int
    songs_without_season: int
    songs_without_genre: int
    songs_without_tag: int
    songs_without_links: int
    anime_without_genre: int
    anime_without_tag: int
    anime_without_season: int


class CoverageCount(TypedDict):
    """Populated records and the total records eligible for a catalog field."""

    present: int
    total: int


class DatabaseStatsPayload(TypedDict):
    database_updated_at: str | None
    total_songs: int
    total_unique_amq_songs: int
    total_anime: int
    total_artists: int
    total_seasons: int
    links_by_type: dict[str, int]
    links_by_coverage: dict[str, int]
    links_by_combination: dict[str, int]
    songs_by_type: dict[str, int]
    songs_by_broadcast: dict[str, int]
    songs_by_performance: dict[str, int]
    songs_by_anime_type: dict[str, int]
    songs_by_difficulty: list[int]
    songs_by_length: list[int]
    songs_by_season: dict[str, int]
    songs_by_genre: dict[str, int]
    songs_by_tag: dict[str, int]
    songs_per_anime: dict[str, int]
    missing_data: DatabaseStatsMissingData
    original_name_coverage: dict[str, CoverageCount]
    external_id_coverage: dict[str, CoverageCount]
    artist_credits: ArtistCreditStatistics
    song_analysis: SongAnalysis


def _season_sort_key(value: str) -> tuple[bool, int, str]:
    """Sort anime seasons chronologically; unknown labels last."""
    index = season_index(value)
    if index is None:
        return (True, 0, value)
    return (False, index, value)


def _original_name_coverage(catalog: Catalog) -> dict[str, CoverageCount]:
    """Count each artist, anime, or song appearance once per populated original field."""
    anime_rows = tuple(anime.songs[0] for anime in catalog.anime_by_id.values())
    coverage: dict[str, CoverageCount] = {
        "artist_aliases": {
            "present": sum(bool(artist.original_names) for artist in catalog.artists_by_id.values()),
            "total": len(catalog.artists_by_id),
        },
        "anime_titles": {
            "present": sum(bool(song.original_jp_name) for song in anime_rows),
            "total": len(anime_rows),
        },
        "anime_alt_titles": {
            "present": sum(bool(song.original_alt_names) for song in anime_rows),
            "total": len(anime_rows),
        },
    }
    for name, field in (
        ("song_titles", "original_song_name"),
        ("performer_names", "original_song_artist"),
        ("composer_names", "original_song_composer"),
        ("arranger_names", "original_song_arranger"),
    ):
        coverage[name] = {
            "present": sum(bool(getattr(song, field)) for song in catalog.song_rows),
            "total": len(catalog.song_rows),
        }
    return coverage


def _external_id_coverage(catalog: Catalog) -> dict[str, CoverageCount]:
    """Count positive list-site IDs per anime and positive song IDs per appearance."""
    anime_rows = tuple(anime.songs[0] for anime in catalog.anime_by_id.values())
    coverage: dict[str, CoverageCount] = {}
    for name, field in (
        ("ann", "ann_id"),
        ("myanimelist", "mal_id"),
        ("anilist", "anilist_id"),
        ("kitsu", "kitsu_id"),
        ("anidb", "anidb_id"),
    ):
        coverage[name] = {
            "present": sum((getattr(song, field) or 0) > 0 for song in anime_rows),
            "total": len(anime_rows),
        }
    for name, rows_by_id in (
        ("ann_song", catalog.songs_by_ann_song_id),
        ("amq_song", catalog.songs_by_amq_song_id),
    ):
        coverage[name] = {
            "present": sum(len(rows) for external_id, rows in rows_by_id.items() if external_id > 0),
            "total": len(catalog.song_rows),
        }
    return coverage


def build_statistics(catalog: Catalog) -> DatabaseStatsPayload:
    song_rows = catalog.song_rows
    artists_by_id = catalog.artists_by_id
    anime_by_id = catalog.anime_by_id
    genres_by_ann_id = catalog.genres_by_ann_id
    tags_by_ann_id = catalog.tags_by_ann_id
    genre_by_lower = catalog.genre_by_lower
    tag_by_lower = catalog.tag_by_lower
    songs_by_ann = catalog.songs_by_ann_id
    song_type_counts: Counter[int] = Counter()
    broadcast_counts: Counter[str] = Counter(
        {"Normal": 0, "Dub": 0, "Rebroadcast": 0, "Dub + Rebroadcast": 0}
    )
    performance_counts: Counter[str] = Counter()
    anime_type_counts: Counter[str] = Counter()
    season_song_counts: Counter[str] = Counter()
    genre_song_counts: Counter[str] = Counter()
    tag_song_counts: Counter[str] = Counter()
    length_counts: Counter[int] = Counter()
    link_combination_counts: Counter[tuple[bool, bool, bool]] = Counter()
    difficulty_counts = [0] * 101
    seasons: set[str] = set()
    anime_ids = anime_by_id.keys()
    hq_count = mq_count = audio_count = 0
    songs_without_difficulty = 0
    songs_without_length = 0
    songs_without_season = 0
    songs_without_genre = 0
    songs_without_tag = 0
    songs_without_links = 0

    for song in song_rows:
        ann_id = song.ann_id
        song_type_counts[song.song_type] += 1
        if song.is_dub and song.is_rebroadcast:
            broadcast = "Dub + Rebroadcast"
        elif song.is_dub:
            broadcast = "Dub"
        elif song.is_rebroadcast:
            broadcast = "Rebroadcast"
        else:
            broadcast = "Normal"
        broadcast_counts[broadcast] += 1
        performance_counts[normalize_song_category(song.song_category)] += 1
        anime_type_counts[normalize_anime_type(song.anime_type)] += 1

        difficulty = song.song_difficulty
        if not song.has_difficulty:
            songs_without_difficulty += 1
        else:
            bucket = int(difficulty)
            if bucket < 0:
                bucket = 0
            elif bucket > 100:
                bucket = 100
            difficulty_counts[bucket] += 1

        length = song.song_length
        if length is None:
            songs_without_length += 1
        else:
            length_counts[int(length)] += 1

        vintage = song.anime_vintage
        if vintage:
            seasons.add(vintage)
            season_song_counts[vintage] += 1
        else:
            songs_without_season += 1

        genres = genres_by_ann_id.get(ann_id)
        if genres:
            for genre in genres:
                genre_song_counts[genre_by_lower[genre.lower()]] += 1
        else:
            songs_without_genre += 1

        tags = tags_by_ann_id.get(ann_id)
        if tags:
            for tag in tags:
                tag_song_counts[tag_by_lower[tag.lower()]] += 1
        else:
            songs_without_tag += 1

        available = song.available_media_links
        has_hq = "hq" in available
        has_mq = "mq" in available
        has_audio = "audio" in available
        link_combination_counts[has_hq, has_mq, has_audio] += 1
        hq_count += has_hq
        mq_count += has_mq
        audio_count += has_audio
        if not (has_hq or has_mq or has_audio):
            songs_without_links += 1

    max_length_seconds = max(length_counts) if length_counts else 0
    songs_by_length = [length_counts.get(seconds, 0) for seconds in range(max_length_seconds + 1)]
    songs_per_anime_counts = Counter(len(rows) for rows in songs_by_ann.values())
    songs_per_anime = {
        str(song_count): anime_count
        for song_count, anime_count in sorted(songs_per_anime_counts.items())
    }
    songs_by_season = {
        season: season_song_counts[season]
        for season in sorted(season_song_counts, key=_season_sort_key)
    }
    songs_by_genre = {
        genre: count
        for genre, count in sorted(
            genre_song_counts.items(), key=lambda item: (-item[1], item[0].lower())
        )
    }
    songs_by_tag = {
        tag: count
        for tag, count in sorted(
            tag_song_counts.items(), key=lambda item: (-item[1], item[0].lower())
        )
    }

    database_stats: DatabaseStatsPayload = {
        "database_updated_at": catalog.database_updated_at,
        "total_songs": len(song_rows),
        "total_unique_amq_songs": sum(external_id > 0 for external_id in catalog.songs_by_amq_song_id),
        "total_anime": len(anime_ids),
        "total_artists": len(artists_by_id),
        "total_seasons": len(seasons),
        "links_by_type": {"HQ": hq_count, "MQ": mq_count, "audio": audio_count},
        "links_by_coverage": {
            "Any video": sum(count for (hq, mq, _), count in link_combination_counts.items() if hq or mq),
            "All three formats": link_combination_counts[True, True, True],
            "No media": songs_without_links,
        },
        "links_by_combination": {
            "HQ + MQ + audio": link_combination_counts[True, True, True],
            "HQ + MQ": link_combination_counts[True, True, False],
            "HQ + audio": link_combination_counts[True, False, True],
            "MQ + audio": link_combination_counts[False, True, True],
            "HQ only": link_combination_counts[True, False, False],
            "MQ only": link_combination_counts[False, True, False],
            "Audio only": link_combination_counts[False, False, True],
            "None": link_combination_counts[False, False, False],
        },
        "songs_by_type": {
            "Opening": song_type_counts[1],
            "Ending": song_type_counts[2],
            "Insert": song_type_counts[3],
        },
        "songs_by_broadcast": dict(broadcast_counts),
        "songs_by_performance": dict(performance_counts),
        "songs_by_anime_type": dict(anime_type_counts),
        "songs_by_difficulty": difficulty_counts,
        "songs_by_length": songs_by_length,
        "songs_by_season": songs_by_season,
        "songs_by_genre": songs_by_genre,
        "songs_by_tag": songs_by_tag,
        "songs_per_anime": songs_per_anime,
        "original_name_coverage": _original_name_coverage(catalog),
        "external_id_coverage": _external_id_coverage(catalog),
        "artist_credits": build_artist_credit_statistics(catalog),
        "song_analysis": build_song_analysis(catalog),
        "missing_data": {
            "songs_without_difficulty": songs_without_difficulty,
            "songs_without_length": songs_without_length,
            "songs_without_season": songs_without_season,
            "songs_without_genre": songs_without_genre,
            "songs_without_tag": songs_without_tag,
            "songs_without_links": songs_without_links,
            "anime_without_genre": sum(1 for ann_id in anime_ids if ann_id not in genres_by_ann_id),
            "anime_without_tag": sum(1 for ann_id in anime_ids if ann_id not in tags_by_ann_id),
            "anime_without_season": sum(1 for anime in anime_by_id.values() if not anime.anime_vintage),
        },
    }
    return database_stats
