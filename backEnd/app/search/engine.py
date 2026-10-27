"""Execute every search operation over the immutable catalog snapshot."""

import random
from collections.abc import Iterable, Sequence
from itertools import islice
from re import Pattern
from typing import assert_never

from catalog.models import Catalog, SearchName, Song, SongMap
from search import credit_matching, text_matching
from search.filters import SongFilters
from search.models import (
    ArtistIdCriteria,
    ArtistSearchFilter,
    ComposerIdCriteria,
    ComposerSearchFilter,
    CreditSearchOptions,
    ExternalIdCriteria,
    IdMatch,
    RandomCriteria,
    SearchQuery,
    SeasonCriteria,
    TextCriteria,
    TextSearchFilter,
)

ArtistIdResolutionCache = dict[tuple[str, bool], list[int]]
MAX_ARTIST_NAME_MATCHES = 50


def search_songs(catalog: Catalog, query: SearchQuery) -> list[Song]:
    """Retrieve candidates and apply the shared duplicate and result-limit policies."""
    criteria = query.criteria
    match criteria:
        case TextCriteria():
            songs = _text_candidates(catalog, criteria, query.filters)
        case ExternalIdCriteria():
            songs = _external_id_candidates(catalog, criteria, query.filters)
        case ArtistIdCriteria():
            songs = _artist_candidates(
                catalog, criteria.ids, criteria.options, query.filters, id_match=criteria.id_match
            )
        case ComposerIdCriteria():
            songs = _composer_candidates(
                catalog,
                criteria.ids,
                criteria.options,
                criteria.arrangement,
                query.filters,
                id_match=criteria.id_match,
            )
        case SeasonCriteria():
            songs = _season_candidates(catalog, criteria.season, query.filters)
        case RandomCriteria():
            return _random_songs(catalog, criteria.count, query)
        case _:
            assert_never(criteria)
    return _select_songs(songs.values(), query.ignore_duplicate, query.limit)


def _songs_by_ids(
    catalog: Catalog,
    song_ids: Sequence[int],
    song_filters: SongFilters,
) -> SongMap:
    """Look up unique songs.id keys and return filtered rows in candidate order."""
    songs: SongMap = {}

    for song_id in song_ids:
        song = catalog.songs_by_id.get(song_id)
        if song is not None and song_filters.matches_row(song):
            songs[song_id] = song

    return songs


def _anime_candidates(
    catalog: Catalog,
    search_filter: TextSearchFilter,
    song_filters: SongFilters,
) -> SongMap:
    """Match romanized, English, and original anime titles and alternate names."""
    anime_regex = text_matching.build_search_regex(
        search_filter.search,
        search_filter.partial_match,
        search_filter.match_case,
    )
    results: SongMap = {}
    for anime in catalog.anime_by_id.values():
        if any(
            anime_regex.search(name.value if search_filter.match_case else name.lowered)
            for name in anime.search_names
        ):
            for song in anime.songs:
                if song_filters.matches_row(song):
                    results[song.song_id] = song

    return results


def _matches_song_text(
    pattern: Pattern[str],
    romaji: str | None,
    original: str | None,
    match_case: bool,
) -> bool:
    """Match display text or its original spelling, skipping duplicate comparisons."""
    return text_matching.regex_matches(pattern, romaji or "", match_case) or bool(
        original
        and original != romaji
        and text_matching.regex_matches(pattern, original, match_case)
    )


def _song_name_candidates(
    catalog: Catalog,
    search_filter: TextSearchFilter,
    song_filters: SongFilters,
) -> SongMap:
    """Regex-match the song title field across the in-memory song database."""
    song_name_regex = text_matching.build_search_regex(
        search_filter.search,
        search_filter.partial_match,
        search_filter.match_case,
    )
    results: SongMap = {}
    for song in catalog.song_rows:
        if _matches_song_text(
            song_name_regex,
            song.romaji_song_name,
            song.original_song_name,
            search_filter.match_case,
        ) and song_filters.matches_row(song):
            results[song.song_id] = song

    return results


def _artist_text_fallback(
    catalog: Catalog,
    artist_regex: Pattern[str],
    match_case: bool,
    song_filters: SongFilters,
    limit: int = 500,
) -> SongMap:
    """Fallback when artist ID resolution finds no matches.

    Matches romanized or original display credits. Catches spellings/guest strings
    missing from the artist aliases. No credit-target filtering; limit 500 because
    text regex can match broadly.
    """
    results: SongMap = {}

    for song in catalog.song_rows:
        if not _matches_song_text(
            artist_regex,
            song.romaji_song_artist,
            song.original_song_artist,
            match_case,
        ):
            continue
        if not song_filters.matches_row(song):
            continue

        results[song.song_id] = song
        if len(results) >= limit:
            break

    return results


def _composer_text_fallback(
    catalog: Catalog,
    composer_regex: Pattern[str],
    match_case: bool,
    arrangement: bool,
    song_filters: SongFilters,
    limit: int = 500,
) -> SongMap:
    """Fallback when composer ID resolution finds no matches.

    Matches romanized or original composer credits, plus arranger credits when enabled.
    No credit-target filtering; limit 500 because text regex can match broadly.
    """
    results: SongMap = {}

    for song in catalog.song_rows:
        if not (
            _matches_song_text(
                composer_regex, song.romaji_song_composer, song.original_song_composer, match_case
            )
            or (
                arrangement
                and _matches_song_text(
                    composer_regex, song.romaji_song_arranger, song.original_song_arranger, match_case
                )
            )
        ):
            continue
        if not song_filters.matches_row(song):
            continue

        results[song.song_id] = song
        if len(results) >= limit:
            break

    return results


def _resolve_artist_ids(
    catalog: Catalog,
    regex: Pattern[str],
    match_case: bool,
    cache: ArtistIdResolutionCache,
) -> list[int]:
    """Resolve a name pattern once per request, including empty results."""
    key = (regex.pattern, match_case)
    if key in cache:
        return cache[key]

    ids: list[int] = []
    seen: set[int] = set()
    for artist_id, name in catalog.artist_name_rows:
        if artist_id in seen or regex.search(name.value if match_case else name.lowered) is None:
            continue
        seen.add(artist_id)
        ids.append(artist_id)
        if len(ids) >= MAX_ARTIST_NAME_MATCHES:
            break
    cache[key] = ids
    return ids


def _artist_name_candidates(
    catalog: Catalog,
    search_filter: ArtistSearchFilter,
    song_filters: SongFilters,
    artist_id_cache: ArtistIdResolutionCache,
) -> SongMap:
    """Resolve artist name to IDs, widen to groups/members, fetch songs, filter by credit rules."""
    artist_regex = text_matching.build_search_regex(
        search_filter.search,
        search_filter.partial_match,
        search_filter.match_case,
        swap_words=True,
    )
    artist_ids = _resolve_artist_ids(
        catalog,
        artist_regex,
        search_filter.match_case,
        artist_id_cache,
    )

    # If no IDs are found, search the denormalized display credit in memory.
    if not artist_ids:
        return _artist_text_fallback(
            catalog,
            artist_regex,
            search_filter.match_case,
            song_filters,
        )

    return _artist_candidates(catalog, artist_ids, search_filter, song_filters)


def _composer_name_candidates(
    catalog: Catalog,
    search_filter: ComposerSearchFilter,
    song_filters: SongFilters,
    artist_id_cache: ArtistIdResolutionCache,
) -> SongMap:
    """Resolve composer name to IDs, widen to groups/members, fetch songs, filter by credit rules."""
    composer_regex = text_matching.build_search_regex(
        search_filter.search,
        search_filter.partial_match,
        search_filter.match_case,
        swap_words=True,
    )
    composer_ids = _resolve_artist_ids(
        catalog,
        composer_regex,
        search_filter.match_case,
        artist_id_cache,
    )

    # If no IDs are found, search the denormalized display credit in memory.
    if not composer_ids:
        return _composer_text_fallback(
            catalog,
            composer_regex,
            search_filter.match_case,
            search_filter.arrangement,
            song_filters,
        )

    return _composer_candidates(
        catalog, composer_ids, search_filter, search_filter.arrangement, song_filters
    )


def _artist_candidates(
    catalog: Catalog,
    artist_ids: Sequence[int],
    options: CreditSearchOptions,
    song_filters: SongFilters,
    *,
    id_match: IdMatch = "any",
) -> SongMap:
    targets = credit_matching.build_artist_credit_targets(catalog, artist_ids)
    if id_match == "all" and any(not group for group in targets):
        return {}
    song_ids = _artist_song_ids(
        catalog,
        credit_matching.expand_search_artist_ids(catalog, artist_ids, options.group_granularity),
    )
    return {
        song_id: song
        for song_id, song in _songs_by_ids(catalog, song_ids, song_filters).items()
        if credit_matching.check_meets_artists_requirements(
            catalog, song, targets, options.group_granularity, options.max_other_artist, id_match
        )
    }


def _composer_candidates(
    catalog: Catalog,
    composer_ids: Sequence[int],
    options: CreditSearchOptions,
    arrangement: bool,
    song_filters: SongFilters,
    *,
    id_match: IdMatch = "any",
) -> SongMap:
    targets = credit_matching.build_composer_credit_targets(catalog, composer_ids)
    if id_match == "all" and any(not group for group in targets):
        return {}
    song_ids = _composer_song_ids(
        catalog,
        credit_matching.expand_search_artist_ids(catalog, composer_ids, options.group_granularity),
        arrangement,
    )
    return {
        song_id: song
        for song_id, song in _songs_by_ids(catalog, song_ids, song_filters).items()
        if credit_matching.check_meets_composers_requirements(
            catalog,
            song,
            targets,
            arrangement,
            options.group_granularity,
            options.max_other_artist,
            id_match,
        )
    }


def _artist_song_ids(catalog: Catalog, artist_ids: Sequence[int]) -> list[int]:
    """Return songs.id values linked to any requested artist ID."""
    return sorted(
        {
            song_id
            for artist_id in set(artist_ids)
            for song_id in catalog.songs_by_artist_id.get(artist_id, ())
        }
    )


def _composer_song_ids(
    catalog: Catalog,
    composer_ids: Sequence[int],
    arrangement: bool,
) -> list[int]:
    """Return songs.id values linked to composer IDs and optionally arranger IDs."""
    reverse_maps = (
        (catalog.songs_by_composer_id, catalog.songs_by_arranger_id)
        if arrangement
        else (catalog.songs_by_composer_id,)
    )
    song_ids = {
        song_id
        for composer_id in set(composer_ids)
        for reverse_map in reverse_maps
        for song_id in reverse_map.get(composer_id, ())
    }
    return sorted(song_ids)


def _text_candidates(catalog: Catalog, criteria: TextCriteria, filters: SongFilters) -> SongMap:
    """Evaluate text branches in legacy order, preserving fallback and limit policies."""
    branch_maps: list[SongMap] = []
    artist_id_cache: ArtistIdResolutionCache = {}

    if text_matching.has_search_text(criteria.anime):
        branch_maps.append(_anime_candidates(catalog, criteria.anime, filters))

    if text_matching.has_search_text(criteria.song_name):
        branch_maps.append(_song_name_candidates(catalog, criteria.song_name, filters))

    if text_matching.has_search_text(criteria.artist):
        branch_maps.append(
            _artist_name_candidates(catalog, criteria.artist, filters, artist_id_cache)
        )

    if text_matching.has_search_text(criteria.composer):
        branch_maps.append(
            _composer_name_candidates(catalog, criteria.composer, filters, artist_id_cache)
        )

    if not branch_maps:
        return {}

    merged_songs: SongMap = {}

    if criteria.and_logic:
        common_ids = set.intersection(*map(set, branch_maps))
        for song_id, song in branch_maps[0].items():
            if song_id in common_ids:
                merged_songs[song_id] = song
    else:
        for branch in branch_maps:
            for song_id, song in branch.items():
                merged_songs.setdefault(song_id, song)

    return merged_songs


def _external_id_candidates(
    catalog: Catalog,
    criteria: ExternalIdCriteria,
    filters: SongFilters,
) -> SongMap:
    index = {
        "ann": catalog.songs_by_ann_id,
        "mal": catalog.songs_by_mal_id,
        "anilist": catalog.songs_by_anilist_id,
        "kitsu": catalog.songs_by_kitsu_id,
        "anidb": catalog.songs_by_anidb_id,
        "ann-song": catalog.songs_by_ann_song_id,
        "amq-song": catalog.songs_by_amq_song_id,
    }[criteria.source]
    rows = (song for external_id in set(criteria.ids) for song in index.get(external_id, ()))
    return {
        song.song_id: song
        for song in sorted(rows, key=lambda song: song.song_id)
        if filters.matches_row(song)
    }


def _season_candidates(catalog: Catalog, season: str, filters: SongFilters) -> SongMap:
    return {
        song.song_id: song
        for song in catalog.songs_by_season.get(season, ())
        if filters.matches_row(song)
    }


def _random_songs(catalog: Catalog, count: int, query: SearchQuery) -> list[Song]:
    candidates = (
        catalog.song_rows
        if query.filters.matches_all()
        else tuple(song for song in catalog.song_rows if query.filters.matches_row(song))
    )
    # Collapse before sampling so duplicates cannot reduce the requested count.
    if query.ignore_duplicate:
        candidates = _select_songs(candidates, ignore_duplicate=True)
    if query.limit is not None:
        count = min(count, query.limit)
    return random.sample(candidates, min(count, len(candidates)))


def _select_songs(
    songs: Iterable[Song],
    ignore_duplicate: bool = False,
    limit: int | None = None,
) -> list[Song]:
    """Apply optional AMQ song duplicate collapse and an output cap."""
    selected: list[Song] = []
    duplicate_indexes: dict[tuple[str, int], int] = {}

    for song in songs:
        if not ignore_duplicate:
            if limit is not None and len(selected) >= limit:
                break
            selected.append(song)
            continue

        # Missing AMQ IDs must not collapse unrelated appearances into one group.
        duplicate_key = (
            ("amq", song.amq_song_id)
            if song.amq_song_id is not None
            else ("row", song.song_id)
        )

        if limit is not None and len(selected) >= limit:
            if duplicate_key not in duplicate_indexes:
                continue

        duplicate_index = duplicate_indexes.get(duplicate_key)
        if duplicate_index is None:
            duplicate_indexes[duplicate_key] = len(selected)
            selected.append(song)
            continue

        if selected[duplicate_index].ann_id > song.ann_id:
            selected[duplicate_index] = song

    return selected


def _autocomplete(
    values: tuple[SearchName, ...], search: str | None, count: int
) -> list[str]:
    """Match pre-normalized values lazily, preserving the catalog's suggestion order."""
    lowered = search.lower() if search else ""
    matches = (entry.value for entry in values if not lowered or lowered in entry.lowered)
    return list(islice(matches, count))


def autocomplete_artists(catalog: Catalog, search: str | None, count: int) -> list[str]:
    return _autocomplete(catalog.artist_autocomplete_values, search, count)


def autocomplete_song_names(catalog: Catalog, search: str | None, count: int) -> list[str]:
    return _autocomplete(catalog.song_name_autocomplete_values, search, count)


def autocomplete_anime_names(
    catalog: Catalog,
    song_name: str | None,
    song_artist: str | None,
) -> list[str]:
    pairs = dict.fromkeys(
        (song.anime_jp_name, song.anime_en_name)
        for song in catalog.song_rows
        if (not song_name or song.romaji_song_name == song_name)
        and (not song_artist or song.romaji_song_artist == song_artist)
    )
    return sorted((jp_name or en_name for jp_name, en_name in pairs), key=str.lower)
