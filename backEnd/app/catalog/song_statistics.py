"""Build grouped song measurements, anime distributions, and vintage/label summaries."""

from collections import Counter, defaultdict
from collections.abc import Iterable
from statistics import fmean
from typing import TypedDict

from catalog.classification import normalize_anime_type, normalize_song_category, season_index
from catalog.models import Catalog, Song

SONG_TYPES = {1: "Opening", 2: "Ending", 3: "Insert"}


class MeasurementSummary(TypedDict):
    known: int
    mean: float | None
    median: float | None
    q1: float | None
    q3: float | None


class SongSummary(TypedDict):
    songs: int
    anime: int
    song_types: dict[str, int]
    difficulty: MeasurementSummary
    length: MeasurementSummary
    media: int


class SongDistribution(TypedDict):
    summary: SongSummary
    difficulty: dict[str, int]
    length: dict[str, int]


class PeriodStatistics(TypedDict):
    overall: SongSummary
    song_type: dict[str, SongSummary]
    anime_format: dict[str, SongSummary]


class TopAnime(TypedDict):
    ann_id: int
    name: str
    songs: int
    song_types: dict[str, int]


class AnimeSongStatistics(TypedDict):
    anime: int
    distribution: dict[str, int]
    median: float | None
    p90: float | None
    maximum: int | None
    most_songs: list[TopAnime]


class SongAnalysis(TypedDict):
    distributions: dict[str, dict[str, SongDistribution]]
    seasons: dict[str, PeriodStatistics]
    years: dict[str, PeriodStatistics]
    songs_per_anime: dict[str, AnimeSongStatistics]
    genres: dict[str, SongSummary]
    tags: dict[str, SongSummary]


def _percentile(values: list[float] | list[int], fraction: float) -> float | None:
    """Interpolate a percentile in a sorted sequence, including one-value groups."""
    if not values:
        return None
    position = (len(values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def _measurement(values: list[float]) -> MeasurementSummary:
    values.sort()
    return {
        "known": len(values),
        "mean": fmean(values) if values else None,
        "median": _percentile(values, 0.5),
        "q1": _percentile(values, 0.25),
        "q3": _percentile(values, 0.75),
    }


def _song_types(rows: Iterable[Song]) -> dict[str, int]:
    counts = Counter(song.song_type for song in rows)
    return {label: counts[kind] for kind, label in SONG_TYPES.items()}


def _summary(rows: list[Song]) -> SongSummary:
    return {
        "songs": len(rows),
        "anime": len({song.ann_id for song in rows}),
        "song_types": _song_types(rows),
        "difficulty": _measurement([song.song_difficulty for song in rows if song.has_difficulty]),
        "length": _measurement([song.song_length for song in rows if song.song_length is not None]),
        "media": sum(bool(song.hq or song.mq or song.audio) for song in rows),
    }


def _histogram(values: Iterable[int]) -> dict[str, int]:
    return {str(value): count for value, count in sorted(Counter(values).items())}


def _distribution(rows: list[Song]) -> SongDistribution:
    return {
        "summary": _summary(rows),
        "difficulty": _histogram(
            min(100, max(0, int(song.song_difficulty))) for song in rows if song.has_difficulty
        ),
        "length": _histogram(
            int(song.song_length) for song in rows if song.song_length is not None
        ),
    }


def _period(rows: list[Song]) -> PeriodStatistics:
    types: defaultdict[str, list[Song]] = defaultdict(list)
    formats: defaultdict[str, list[Song]] = defaultdict(list)
    for song in rows:
        types[SONG_TYPES.get(song.song_type, "Other")].append(song)
        formats[normalize_anime_type(song.anime_type)].append(song)
    return {
        "overall": _summary(rows),
        "song_type": {label: _summary(group) for label, group in sorted(types.items())},
        "anime_format": {label: _summary(group) for label, group in sorted(formats.items())},
    }


def _anime_statistics(catalog: Catalog, anime_ids: list[int]) -> AnimeSongStatistics:
    counts = sorted(len(catalog.anime_by_id[ann_id].songs) for ann_id in anime_ids)
    ordered = sorted(
        anime_ids, key=lambda ann_id: (-len(catalog.anime_by_id[ann_id].songs), ann_id)
    )
    most_songs: list[TopAnime] = []
    for ann_id in ordered[:10]:
        anime = catalog.anime_by_id[ann_id]
        most_songs.append(
            {
                "ann_id": ann_id,
                "name": anime.anime_jp_name or anime.anime_en_name or str(ann_id),
                "songs": len(anime.songs),
                "song_types": _song_types(anime.songs),
            }
        )
    return {
        "anime": len(anime_ids),
        "distribution": _histogram(counts),
        "median": _percentile(counts, 0.5),
        "p90": _percentile(counts, 0.9),
        "maximum": max(counts) if counts else None,
        "most_songs": most_songs,
    }


def build_song_analysis(catalog: Catalog) -> SongAnalysis:
    """Compute cached aggregates from appearances; unknown measurements stay excluded."""
    dimensions: dict[str, defaultdict[str, list[Song]]] = {
        key: defaultdict(list) for key in ("song_type", "performance", "anime_format", "decade")
    }
    seasons: defaultdict[str, list[Song]] = defaultdict(list)
    years: defaultdict[str, list[Song]] = defaultdict(list)
    labels = {"genres": defaultdict(list), "tags": defaultdict(list)}
    for song in catalog.song_rows:
        dimensions["song_type"][SONG_TYPES.get(song.song_type, "Other")].append(song)
        dimensions["performance"][normalize_song_category(song.song_category)].append(song)
        dimensions["anime_format"][normalize_anime_type(song.anime_type)].append(song)
        index = season_index(song.anime_vintage)
        if index is not None:
            year = index // 4
            dimensions["decade"][f"{year // 10 * 10}s"].append(song)
        else:
            dimensions["decade"]["Unknown"].append(song)
        if song.anime_vintage:
            seasons[song.anime_vintage].append(song)
            years[str(index // 4) if index is not None else "Unknown"].append(song)
        for key, by_anime, canonical in (
            ("genres", catalog.genres_by_ann_id, catalog.genre_by_lower),
            ("tags", catalog.tags_by_ann_id, catalog.tag_by_lower),
        ):
            for label in by_anime.get(song.ann_id, ()):
                labels[key][canonical[label.lower()]].append(song)
    anime_formats: defaultdict[str, list[int]] = defaultdict(list)
    for ann_id, anime in catalog.anime_by_id.items():
        anime_formats[normalize_anime_type(anime.anime_type)].append(ann_id)

    def season_key(label: str) -> tuple[bool, int, str]:
        index = season_index(label)
        return (index is None, index or 0, label)

    return {
        "distributions": {
            "all": {"All": _distribution(list(catalog.song_rows))},
            **{
                key: {label: _distribution(rows) for label, rows in sorted(groups.items())}
                for key, groups in dimensions.items()
            },
        },
        "seasons": {
            label: _period(rows)
            for label, rows in sorted(seasons.items(), key=lambda item: season_key(item[0]))
        },
        "years": {label: _period(rows) for label, rows in sorted(years.items())},
        "songs_per_anime": {
            "All": _anime_statistics(catalog, list(catalog.anime_by_id)),
            **{
                label: _anime_statistics(catalog, ids)
                for label, ids in sorted(anime_formats.items())
            },
        },
        "genres": {label: _summary(rows) for label, rows in sorted(labels["genres"].items())},
        "tags": {label: _summary(rows) for label, rows in sorted(labels["tags"].items())},
    }
