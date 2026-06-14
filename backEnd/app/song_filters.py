"""Resolved song/anime type filter lists from API request booleans."""

from dataclasses import dataclass
from typing import Any

ALL_SONG_TYPES = frozenset({1, 2, 3})
ALL_BROADCASTS = frozenset({"Normal", "Dub", "Rebroadcast"})
ALL_SONG_CATEGORIES = frozenset({"Standard", "No Category", "Chanting", "Instrumental", "Character"})
ALL_ANIME_TYPES = frozenset({"TV", "Movie", "OVA", "ONA", "Special", "Doujin"})

# songsFull column indices for in-memory row checks (matches songsFull SELECT * order).
COL_ANIME_TYPE = 11
COL_SONG_TYPE = 16
COL_SONG_CATEGORY = 18
COL_IS_DUB = 34
COL_IS_REBROADCAST = 35


def _has_every_filter(selected, all_values) -> bool:
    """True when selected values cover the full known set, so filtering is unnecessary."""
    return all_values.issubset(selected)


def _in_sql(column: str, selected: list[Any], all_values) -> tuple[str | None, list[Any]]:
    """SQL IN-clause for one filter column, skipped when every known value is selected."""
    if not selected:
        return "0=1", []

    if _has_every_filter(selected, all_values):
        return None, []

    placeholders = ",".join("?" * len(selected))
    return f"{column} IN ({placeholders})", list(selected)


def _value_matches_filter(value, selected, all_values) -> bool:
    """In-memory equivalent of _in_sql for one filter value."""
    if not selected:
        return False
    if _has_every_filter(selected, all_values):
        return True
    return value in selected


def _broadcast_sql(broadcasts: list[str]) -> list[str]:
    """SQL clauses for dub/rebroadcast filtering on songsFull."""
    if not broadcasts:
        return ["0=1"]

    if _has_every_filter(broadcasts, ALL_BROADCASTS):
        return []

    conditions = []

    if "Normal" not in broadcasts:
        conditions.append("(isDub == 1 OR isRebroadcast == 1)")

    if "Dub" not in broadcasts:
        conditions.append("isDub == 0")

    if "Rebroadcast" not in broadcasts:
        conditions.append("isRebroadcast == 0")

    return conditions


@dataclass(frozen=True)
class SongFilterSqlParts:
    """Decomposed SQL fragments for songsFull filter columns."""
    clauses: tuple[str, ...]
    params: tuple[Any, ...]


@dataclass(frozen=True)
class SongFilters:
    song_types: list[int]
    broadcasts: list[str]
    song_categories: list[str]
    anime_types: list[str]

    def matches_row(self, song) -> bool:
        """True when a raw songsFull row matches these filters (same rules as sql_parts())."""
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

            if (not is_dub and not is_rebroadcast) and "Normal" not in self.broadcasts:
                return False

            if is_dub and "Dub" not in self.broadcasts:
                if not is_rebroadcast or "Rebroadcast" not in self.broadcasts:
                    return False

            if is_rebroadcast and "Rebroadcast" not in self.broadcasts:
                return False

        if not _value_matches_filter(
            song[COL_ANIME_TYPE], self.anime_types, ALL_ANIME_TYPES
        ):
            return False

        return True

    def sql_parts(self) -> SongFilterSqlParts:
        """SQL fragments + bind params for songsFull type/broadcast/anime/category filters."""
        clauses: list[str] = []
        params: list[Any] = []

        for column, selected, all_values in (
            ("songType", self.song_types, ALL_SONG_TYPES),
            ("animeType", self.anime_types, ALL_ANIME_TYPES),
            ("songCategory", self.song_categories, ALL_SONG_CATEGORIES),
        ):
            clause, clause_params = _in_sql(column, selected, all_values)
            if clause is not None:
                clauses.append(clause)
                params.extend(clause_params)

        clauses.extend(_broadcast_sql(self.broadcasts))

        return SongFilterSqlParts(clauses=tuple(clauses), params=tuple(params))

    def songs_full_where(
        self, *, middle_sql: str = "", middle_params: list[Any] | None = None
    ) -> tuple[str, list[Any]]:
        """Build a WHERE body from active filters plus an optional endpoint predicate."""
        parts = self.sql_parts()
        clauses = list(parts.clauses)
        params = list(parts.params)

        if middle_sql:
            clauses.append(middle_sql.removeprefix(" AND ").strip())
            params.extend(middle_params or [])

        return " AND ".join(clauses or ["1=1"]), params
