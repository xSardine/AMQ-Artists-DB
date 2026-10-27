"""Normalized song filters and eligibility rules."""

from dataclasses import dataclass, field

from catalog.classification import (
    ALL_ANIME_TYPES,
    ALL_BROADCASTS,
    ALL_SONG_CATEGORIES,
    ALL_SONG_TYPES,
    normalize_anime_type,
    normalize_song_category,
    season_index,
)
from catalog.models import AnimeLabelsByAnnId, Song


def _has_every_filter(selected, all_values) -> bool:
    """True when selected values cover the full known set, so filtering is unnecessary."""
    return all_values.issubset(selected)


def _value_matches_filter(value, selected, all_values) -> bool:
    """Return whether one row value is allowed by a selected filter list."""
    if not selected:
        return False
    if _has_every_filter(selected, all_values):
        return True
    return value in selected


@dataclass(frozen=True)
class MediaLinksRequirements:
    require_any: frozenset[str]
    require_all: frozenset[str]
    exclude: frozenset[str]

    def is_empty(self) -> bool:
        return not (self.require_any or self.require_all or self.exclude)

    def matches(self, song: Song) -> bool:
        available = song.available_media_links
        if self.require_any and self.require_any.isdisjoint(available):
            return False
        if not self.require_all <= available:
            return False
        return self.exclude.isdisjoint(available)


@dataclass(frozen=True)
class LabelSetRequirements:
    """Anime genre/tag membership rules (same shape as media_links)."""

    require_any: frozenset[str]
    require_all: frozenset[str]
    exclude: frozenset[str]

    def is_empty(self) -> bool:
        return not (self.require_any or self.require_all or self.exclude)

    def matches(self, available: frozenset[str]) -> bool:
        if self.require_any and self.require_any.isdisjoint(available):
            return False
        if self.require_all and not self.require_all <= available:
            return False
        if self.exclude and not self.exclude.isdisjoint(available):
            return False
        return True


@dataclass(frozen=True)
class SongFilters:
    song_types: frozenset[int] = ALL_SONG_TYPES
    broadcasts: frozenset[str] = ALL_BROADCASTS
    song_categories: frozenset[str] = ALL_SONG_CATEGORIES
    anime_types: frozenset[str] = ALL_ANIME_TYPES
    season_start: str | None = None
    season_end: str | None = None
    difficulty_start: float | None = None
    difficulty_end: float | None = None
    include_no_difficulty: bool = False
    song_length_start: float | None = None
    song_length_end: float | None = None
    include_no_length: bool = False
    media_links: MediaLinksRequirements | None = None
    genres: LabelSetRequirements | None = None
    tags: LabelSetRequirements | None = None
    genres_by_ann_id: AnimeLabelsByAnnId = field(default_factory=dict)
    tags_by_ann_id: AnimeLabelsByAnnId = field(default_factory=dict)

    _season_start_index: int | None = field(init=False, repr=False)
    _season_end_index: int | None = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Resolve and order query bounds once, rather than for each candidate row.
        start = season_index(self.season_start)
        end = season_index(self.season_end)
        if start is not None and end is not None and start > end:
            season_start, season_end = self.season_end, self.season_start
            object.__setattr__(self, "season_start", season_start)
            object.__setattr__(self, "season_end", season_end)
            start, end = end, start
        object.__setattr__(self, "_season_start_index", start)
        object.__setattr__(self, "_season_end_index", end)

        if (
            self.difficulty_start is not None
            and self.difficulty_end is not None
            and self.difficulty_start > self.difficulty_end
        ):
            difficulty_start, difficulty_end = self.difficulty_end, self.difficulty_start
            object.__setattr__(self, "difficulty_start", difficulty_start)
            object.__setattr__(self, "difficulty_end", difficulty_end)

        if (
            self.song_length_start is not None
            and self.song_length_end is not None
            and self.song_length_start > self.song_length_end
        ):
            song_length_start, song_length_end = self.song_length_end, self.song_length_start
            object.__setattr__(self, "song_length_start", song_length_start)
            object.__setattr__(self, "song_length_end", song_length_end)

    def matches_all(self) -> bool:
        """Return whether every known filter value is enabled."""
        return (
            _has_every_filter(self.song_types, ALL_SONG_TYPES)
            and _has_every_filter(self.broadcasts, ALL_BROADCASTS)
            and _has_every_filter(self.song_categories, ALL_SONG_CATEGORIES)
            and _has_every_filter(self.anime_types, ALL_ANIME_TYPES)
            and self.season_start is None
            and self.season_end is None
            and self.difficulty_start is None
            and self.difficulty_end is None
            and not self.include_no_difficulty
            and self.song_length_start is None
            and self.song_length_end is None
            and not self.include_no_length
            and (self.media_links is None or self.media_links.is_empty())
            and (self.genres is None or self.genres.is_empty())
            and (self.tags is None or self.tags.is_empty())
        )

    def matches_row(self, song: Song) -> bool:
        """True when a normalized song matches these filters."""
        if self.media_links is not None and not self.media_links.matches(song):
            return False

        if self.genres is not None and not self.genres.is_empty():
            available = self.genres_by_ann_id.get(song.ann_id, frozenset())
            if not self.genres.matches(available):
                return False

        if self.tags is not None and not self.tags.is_empty():
            available = self.tags_by_ann_id.get(song.ann_id, frozenset())
            if not self.tags.matches(available):
                return False

        if self.season_start or self.season_end:
            song_season = season_index(song.anime_vintage)
            if song_season is None:
                return False

            start = self._season_start_index
            end = self._season_end_index
            if start is not None and song_season < start:
                return False
            if end is not None and song_season > end:
                return False

        difficulty = song.song_difficulty
        has_difficulty = song.has_difficulty
        if self.difficulty_start is not None or self.difficulty_end is not None:
            if not has_difficulty:
                if not self.include_no_difficulty:
                    return False
            else:
                start = self.difficulty_start
                end = self.difficulty_end
                if start is not None and difficulty < start:
                    return False
                if end is not None and difficulty > end:
                    return False
        elif self.include_no_difficulty and has_difficulty:
            return False

        song_length = song.song_length
        has_length = song_length is not None
        if self.song_length_start is not None or self.song_length_end is not None:
            if not has_length:
                if not self.include_no_length:
                    return False
            else:
                start = self.song_length_start
                end = self.song_length_end
                if start is not None and song_length < start:
                    return False
                if end is not None and song_length > end:
                    return False
        elif self.include_no_length and has_length:
            return False

        if not _value_matches_filter(song.song_type, self.song_types, ALL_SONG_TYPES):
            return False

        if not _value_matches_filter(
            normalize_song_category(song.song_category),
            self.song_categories,
            ALL_SONG_CATEGORIES,
        ):
            return False

        if not _has_every_filter(self.broadcasts, ALL_BROADCASTS):
            is_dub = bool(song.is_dub)
            is_rebroadcast = bool(song.is_rebroadcast)
            if not is_dub and not is_rebroadcast:
                if "Normal" not in self.broadcasts:
                    return False
            elif is_dub and not is_rebroadcast:
                if "Dub" not in self.broadcasts:
                    return False
            elif not is_dub and is_rebroadcast:
                if "Rebroadcast" not in self.broadcasts:
                    return False
            elif "Dub" not in self.broadcasts and "Rebroadcast" not in self.broadcasts:
                return False

        if not _value_matches_filter(
            normalize_anime_type(song.anime_type),
            self.anime_types,
            ALL_ANIME_TYPES,
        ):
            return False

        return True
