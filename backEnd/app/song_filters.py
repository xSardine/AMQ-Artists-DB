"""Resolved song/anime type filter lists from API request booleans."""

from dataclasses import dataclass

from db_types import *

ALL_SONG_TYPES = frozenset({1, 2, 3})
ALL_BROADCASTS = frozenset({"Normal", "Dub", "Rebroadcast"})
ALL_SONG_CATEGORIES = frozenset({"Standard", "No Category", "Chanting", "Instrumental", "Character"})
ALL_ANIME_TYPES = frozenset({"TV", "Movie", "OVA", "ONA", "Special", "Doujin"})


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
class SongFilters:
    song_types: list[int]
    broadcasts: list[str]
    song_categories: list[str]
    anime_types: list[str]

    def matches_all(self) -> bool:
        """Return whether every known filter value is enabled."""
        return (
            _has_every_filter(self.song_types, ALL_SONG_TYPES)
            and _has_every_filter(self.broadcasts, ALL_BROADCASTS)
            and _has_every_filter(self.song_categories, ALL_SONG_CATEGORIES)
            and _has_every_filter(self.anime_types, ALL_ANIME_TYPES)
        )

    def matches_row(self, song: SongFullRow) -> bool:
        """True when a raw songsFull row matches these filters."""
        if not _value_matches_filter(
            song[COL_SONG_TYPE], self.song_types, ALL_SONG_TYPES
        ):
            return False

        if not _value_matches_filter(
            song[COL_SONG_CATEGORY], self.song_categories, ALL_SONG_CATEGORIES
        ):
            return False

        if not _has_every_filter(self.broadcasts, ALL_BROADCASTS):
            is_dub = bool(song[COL_IS_DUB])
            is_rebroadcast = bool(song[COL_IS_REBROADCAST])
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
            song[COL_ANIME_TYPE], self.anime_types, ALL_ANIME_TYPES
        ):
            return False

        return True
