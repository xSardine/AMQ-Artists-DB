"""Define canonical categories and interpret anime season labels."""

import re
from functools import cache

ALL_SONG_TYPES = frozenset({1, 2, 3})
ALL_BROADCASTS = frozenset({"Normal", "Dub", "Rebroadcast"})
CANONICAL_SONG_CATEGORIES = frozenset({"Standard", "Character", "Chanting", "Instrumental"})
OTHER_SONG_CATEGORY = "Other"
ALL_SONG_CATEGORIES = CANONICAL_SONG_CATEGORIES | {OTHER_SONG_CATEGORY}
CANONICAL_ANIME_TYPES = frozenset({"TV", "Movie", "OVA", "ONA", "Special"})
OTHER_ANIME_TYPE = "Other"
ALL_ANIME_TYPES = CANONICAL_ANIME_TYPES | {OTHER_ANIME_TYPE}
SEASON_ORDER = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}


def normalize_song_category(value: str | None) -> str:
    """Map DB songCategory to a filter bucket; No Category/unknown/missing become Other."""
    if value in CANONICAL_SONG_CATEGORIES:
        return value
    return OTHER_SONG_CATEGORY


def normalize_anime_type(value: str | None) -> str:
    """Map DB animeType to a filter bucket; Doujin/unknown/missing become Other."""
    if value in CANONICAL_ANIME_TYPES:
        return value
    return OTHER_ANIME_TYPE


@cache
def season_index(value: str | None) -> int | None:
    """Map 'Season YYYY' to a comparable int; None if missing or malformed."""
    if not value:
        return None
    match = re.fullmatch(r"(Winter|Spring|Summer|Fall) (\d{4})", value.strip())
    if not match:
        return None
    return int(match.group(2)) * 4 + SEASON_ORDER[match.group(1)]
