import utils
from collections.abc import Iterable
from re import Pattern

from catalog import Catalog
from db_types import *
from schemas import ArtistSearchFilter, ComposerSearchFilter, TextSearchFilter
from song_filters import SongFilters

# Artist IDs for groups that have vocalist line-ups, but some songs credit the
# group itself with line_up=-1 instead of a specific roster.
# Large rotating choirs, theater casts, collectives, anime-specific groups.
LINE_UP_EXCEPTIONS = frozenset(
    {
        33,     # Tokyo Konsei Gasshou-dan
        215,    # Suginami Jidou Gasshou-dan
        19619,  # It's Follies
        23630,  # Hanamaru Gakudan
        466,    # Mori no Ki Jidou Gasshou-dan
        546,    # Pokemon Kids
        1736,   # Falcom Sound Team jdk
        1639,   # system-B
        8086,   # IPD voice
        20185,  # School Mates
        4261,   # supercell
        7695,   # millennium parade
        6678,   # MOB CHOIR
        5611,   # Uchuujin
    }
)

def _select_songs(
    songs: SongMap,
    ignore_duplicate: bool = False,
    max_nb_songs: int | None = None,
) -> list[SongFullRow]:
    """Apply optional title/artist duplicate collapse and an output cap."""
    selected: list[SongFullRow] = []
    duplicate_indexes: dict[tuple[str, str], int] = {}

    for song in songs.values():
        if not ignore_duplicate:
            if max_nb_songs is not None and len(selected) >= max_nb_songs:
                break
            selected.append(song)
            continue

        duplicate_key = (song[COL_ROMAJI_SONG_NAME], song[COL_ROMAJI_SONG_ARTIST] or "")

        if max_nb_songs is not None and len(selected) >= max_nb_songs:
            if duplicate_key not in duplicate_indexes:
                continue

        duplicate_index = duplicate_indexes.get(duplicate_key)
        if duplicate_index is None:
            duplicate_indexes[duplicate_key] = len(selected)
            selected.append(song)
            continue

        if selected[duplicate_index][COL_ANN_ID] > song[COL_ANN_ID]:
            selected[duplicate_index] = song

    return selected


def _format_songs(
    catalog: Catalog,
    songs: Iterable[SongFullRow],
) -> list[FormattedSong]:
    """Convert selected raw rows to API response dicts."""
    return [utils.format_song(catalog.artists_by_id, song) for song in songs]


def _parse_credits(ids_col: str, line_up_col: str) -> Credits:
    """Parse parallel comma-separated credit columns into an immutable credit tuple."""
    if not ids_col:
        return ()
    return tuple(
        (int(credit_id), int(line_up))
        for credit_id, line_up in zip(ids_col.split(","), line_up_col.split(","))
    )


def _build_artist_credit_targets(
    catalog: Catalog,
    artist_ids: list[int],
) -> list[CreditTarget]:
    """Precompute flattened vocalist line-ups for matched artist IDs (once per search)."""
    targets: list[CreditTarget] = []

    for artist_id in artist_ids:
        line_ups: list[Credits] = [((artist_id, -1),)]
        artist = catalog.artists_by_id.get(str(artist_id))
        if not artist:
            continue

        if artist["line_ups"]:
            line_ups = [
                line_up["members"]
                for line_up in artist["line_ups"]
                if line_up["line_up_type"] == "vocalists"
            ]
            if artist_id in LINE_UP_EXCEPTIONS:
                line_ups.append(((artist_id, -1),))

        for line_up in line_ups:
            targets.append(
                CreditTarget(len(line_up), catalog.flatten_credits(line_up))
            )

    return targets


def _build_composer_credit_targets(
    catalog: Catalog,
    composer_ids: list[int],
) -> list[CreditTarget]:
    """Precompute flattened composer line-ups for matched composer IDs (once per search)."""

    # TODO: Composer and arranger searches currently consider every group line-up.
    # Ideally they should use only line-ups whose type is `composers`, but many
    # legacy groups have composer/arranger credits without a composer-specific
    # roster. Filtering strictly would make those groups stop expanding to their
    # members. Prefer composer line-ups when available and retain vocalist line-ups
    # only as a fallback until the source data has been fully curated.

    targets: list[CreditTarget] = []

    for composer_id in composer_ids:
        line_ups: list[Credits] = [((composer_id, -1),)]
        artist = catalog.artists_by_id.get(str(composer_id))
        if not artist:
            continue

        # TODO: Uncomment when more composer line-ups exist
        if artist["line_ups"]:
            line_ups = [
                line_up["members"]
                for line_up in artist["line_ups"]
                # if line_up["line_up_type"] == "composers"
            ]
            # if composer_id in LINE_UP_EXCEPTIONS:
            line_ups.append(((composer_id, -1),))

        for line_up in line_ups:
            targets.append(
                CreditTarget(len(line_up), catalog.flatten_credits(line_up))
            )

    return targets


def _credits_match_targets(
    song_credits_flat: frozenset[int],
    credit_targets: list[CreditTarget],
    group_granularity: int,
    max_other_artist: int,
) -> bool:
    """True if song credits overlap any search target enough for group_granularity rules."""
    for target in credit_targets:
        present_artist = len(song_credits_flat & target.members_flat)
        if present_artist < 1:
            continue
        additional_artist = len(song_credits_flat - target.members_flat)
        if (
            additional_artist <= max_other_artist
            and present_artist >= min(group_granularity, target.line_up_len)
        ):
            return True

    return False


def _check_meets_artists_requirements(
    catalog: Catalog,
    song: SongFullRow,
    credit_targets: list[CreditTarget],
    group_granularity: int,
    max_other_artist: int,
) -> bool:
    """True if the song's credited performers satisfy the artist search constraints."""
    return _credits_match_targets(
        catalog.flatten_credits(
            _parse_credits(song[COL_ARTISTS], song[COL_ARTISTS_LINE_UP])
        ),
        credit_targets,
        group_granularity,
        max_other_artist,
    )


def _check_meets_composers_requirements(
    catalog: Catalog,
    song: SongFullRow,
    credit_targets: list[CreditTarget],
    arrangement: bool,
    group_granularity: int,
    max_other_artist: int,
) -> bool:
    """True if the song's composer/arranger credits satisfy the composer search constraints."""
    song_composers: list[CreditPair] = []
    if song[COL_COMPOSERS]:
        song_composers.extend(_parse_credits(song[COL_COMPOSERS], song[COL_COMPOSERS_LINE_UP]))
    if arrangement and song[COL_ARRANGERS]:
        song_composers.extend(_parse_credits(song[COL_ARRANGERS], song[COL_ARRANGERS_LINE_UP]))

    return _credits_match_targets(
        catalog.flatten_credits(tuple(song_composers)),
        credit_targets,
        group_granularity,
        max_other_artist,
    )


def _get_songs_from_song_ids(
    catalog: Catalog,
    song_ids: list[int],
    song_filters: SongFilters,
) -> SongMap:
    """Look up unique songs.id keys and return filtered rows in candidate order."""
    songs: SongMap = {}

    for song_id in song_ids:
        song = catalog.songs_by_id.get(song_id)
        if song is not None and song_filters.matches_row(song):
            songs[song_id] = song

    return songs


def _expand_search_artist_ids(
    catalog: Catalog,
    root_ids: list[int],
    group_granularity: int,
) -> list[int]:
    """Widen regex-matched artist IDs before reverse-map song lookup.

    Includes parent groups, and when group_granularity > 0 also expands line-up
    members so songs credited to sub-units are found.
    """
    root_id_set = set(root_ids)
    line_up_member_ids: set[int] = set()

    if group_granularity > 0:
        for artist_id in root_ids:
            artist_entry = catalog.artists_by_id.get(str(artist_id))
            if artist_entry:
                for line_up in artist_entry["line_ups"]:
                    line_up_member_ids.update(
                        catalog.flatten_credits(line_up["members"], False)
                    )

    parent_group_ids = {
        group_id
        for artist_id in root_id_set | line_up_member_ids
        for group_id, _ in _get_all_groups(artist_id, catalog.artists_by_id)
    }

    return list(root_id_set | line_up_member_ids | parent_group_ids)


def _get_all_groups(
    artist_id: int,
    artist_database: ArtistDatabase,
    include_composers_groups: bool = False,
) -> list[tuple[int, int]]:
    """Recursively list every parent group (group_id, line_up) for an artist."""
    entry = artist_database.get(str(artist_id))
    if not entry:
        return []

    # TODO: The 'include_composers_groups' parameter is currently unused
    # Might be a problem in the long run to take into account composers groups
    groups: list[tuple[int, int]] = []
    for group in entry["groups"]:
        group_id, line_up = group[0], group[1]
        groups.append((group_id, line_up))
        groups.extend(_get_all_groups(group_id, artist_database, include_composers_groups))

    return groups


def _search_anime_songs(
    catalog: Catalog,
    search_filter: TextSearchFilter,
    song_filters: SongFilters,
) -> SongMap:
    """Regex-match anime JP/EN/alt names, return filtered songs from matching anime."""
    anime_regex = utils.build_search_regex(
        search_filter.search,
        search_filter.partial_match,
        search_filter.match_case,
    )
    results: SongMap = {}
    for anime in catalog.anime_by_id.values():
        names = [anime["animeJPName"], anime["animeENName"]]
        alt = anime.get("animeAltNames")
        if alt:
            names.extend(alt.split("\\$"))
        if any(
            name
            and utils.regex_matches(anime_regex, name, search_filter.match_case)
            for name in names
        ):
            for song in anime["songs"]:
                if song_filters.matches_row(song):
                    results[song[COL_SONG_ID]] = song

    return results


def _search_song_name_songs(
    catalog: Catalog,
    search_filter: TextSearchFilter,
    song_filters: SongFilters,
) -> SongMap:
    """Regex-match the song title field across the in-memory song database."""
    song_name_regex = utils.build_search_regex(
        search_filter.search,
        search_filter.partial_match,
        search_filter.match_case,
    )
    results: SongMap = {}
    for song in catalog.song_rows:
        if utils.regex_matches(
            song_name_regex,
            song[COL_ROMAJI_SONG_NAME],
            search_filter.match_case,
        ) and song_filters.matches_row(song):
            results[song[COL_SONG_ID]] = song

    return results


def _search_song_artist_text(
    catalog: Catalog,
    artist_regex: Pattern[str],
    match_case: bool,
    song_filters: SongFilters,
    limit: int = 500,
) -> SongMap:
    """Fallback when artist ID resolution finds no matches.

    Matches romajiSongArtist on cached songsFull rows (display credit, not structured
    IDs). Catches spellings/guest strings missing from the artist DB. No credit-target
    filtering; limit 500 because text regex can match broadly.
    """
    results: SongMap = {}

    for song in catalog.song_rows:
        if not utils.regex_matches(
            artist_regex,
            song[COL_ROMAJI_SONG_ARTIST] or "",
            match_case,
        ):
            continue
        if not song_filters.matches_row(song):
            continue

        results[song[COL_SONG_ID]] = song
        if len(results) >= limit:
            break

    return results


def _resolve_artist_ids(
    catalog: Catalog,
    regex: Pattern[str],
    match_case: bool,
    artist_id_cache: ArtistIdResolutionCache | None,
) -> list[int]:
    """Resolve an artist-name pattern once per request, including empty results."""
    if artist_id_cache is None:
        return catalog.resolve_artist_ids(regex, match_case)

    key = (regex.pattern, match_case)
    if key not in artist_id_cache:
        artist_id_cache[key] = catalog.resolve_artist_ids(regex, match_case)
    return artist_id_cache[key]


def _search_artist_songs(
    catalog: Catalog,
    search_filter: ArtistSearchFilter,
    song_filters: SongFilters,
    artist_id_cache: ArtistIdResolutionCache | None = None,
) -> SongMap:
    """Resolve artist name to IDs, widen to groups/members, fetch songs, filter by credit rules."""
    artist_regex = utils.build_search_regex(
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
        return _search_song_artist_text(
            catalog,
            artist_regex,
            search_filter.match_case,
            song_filters,
        )

    song_ids = catalog.song_ids_for_artists(
        _expand_search_artist_ids(
            catalog,
            artist_ids,
            search_filter.group_granularity,
        ),
    )

    credit_targets = _build_artist_credit_targets(catalog, artist_ids)

    return {
        song_id: song
        for song_id, song in _get_songs_from_song_ids(
            catalog, song_ids, song_filters
        ).items()
        if _check_meets_artists_requirements(
            catalog,
            song,
            credit_targets,
            search_filter.group_granularity,
            search_filter.max_other_artist,
        )
    }


def _search_composer_songs(
    catalog: Catalog,
    search_filter: ComposerSearchFilter,
    song_filters: SongFilters,
    artist_id_cache: ArtistIdResolutionCache | None = None,
) -> SongMap:
    """Resolve composer name to IDs, widen to groups/members, fetch songs, filter by credit rules."""
    composer_regex = utils.build_search_regex(
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

    # If no IDs found, skip romajiSongComposer fallback (unlike artist search; saves compute time).
    if not composer_ids:
        return {}

    song_ids = catalog.song_ids_for_composers(
        _expand_search_artist_ids(
            catalog, composer_ids, search_filter.group_granularity
        ),
        search_filter.arrangement,
    )

    credit_targets = _build_composer_credit_targets(catalog, composer_ids)

    return {
        song_id: song
        for song_id, song in _get_songs_from_song_ids(catalog, song_ids, song_filters).items()
        if _check_meets_composers_requirements(
            catalog,
            song,
            credit_targets,
            search_filter.arrangement,
            search_filter.group_granularity,
            search_filter.max_other_artist,
        )
    }


def get_search_results(
    catalog: Catalog,
    anime_search_filter: TextSearchFilter | None,
    song_name_search_filter: TextSearchFilter | None,
    artist_search_filter: ArtistSearchFilter | None,
    composer_search_filter: ComposerSearchFilter | None,
    and_logic: bool,
    ignore_duplicate: bool,
    max_nb_songs: int | None,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """Main /api/search_request pipeline: run each active text filter, then merge results."""

    branch_maps: list[SongMap] = []
    artist_id_cache: ArtistIdResolutionCache = {}

    if utils.has_search_text(anime_search_filter):
        branch_maps.append(
            _search_anime_songs(
                catalog, anime_search_filter, song_filters
            )
        )

    if utils.has_search_text(song_name_search_filter):
        branch_maps.append(
            _search_song_name_songs(
                catalog, song_name_search_filter, song_filters
            )
        )

    if utils.has_search_text(artist_search_filter):
        branch_maps.append(
            _search_artist_songs(
                catalog, artist_search_filter, song_filters, artist_id_cache
            )
        )

    if utils.has_search_text(composer_search_filter):
        branch_maps.append(
            _search_composer_songs(
                catalog, composer_search_filter, song_filters, artist_id_cache
            )
        )

    if not branch_maps:
        return []

    merged_songs: SongMap = {}

    if and_logic:
        common_ids = set.intersection(*map(set, branch_maps))
        for song_id, song in branch_maps[0].items():
            if song_id in common_ids:
                merged_songs[song_id] = song
    else:
        for branch in branch_maps:
            for song_id, song in branch.items():
                merged_songs.setdefault(song_id, song)

    return _format_songs(
        catalog,
        _select_songs(merged_songs, ignore_duplicate, max_nb_songs),
    )


def get_artist_ids_song_list(
    catalog: Catalog,
    artist_ids: list[int],
    group_granularity: int,
    max_other_artist: int,
    ignore_duplicate: bool,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """Songs credited to explicit artist IDs (and their groups), without name-regex search."""
    if not artist_ids:
        return []

    song_ids = catalog.song_ids_for_artists(
        _expand_search_artist_ids(catalog, artist_ids, group_granularity),
    )

    credit_targets = _build_artist_credit_targets(catalog, artist_ids)

    songs = {
        song_id: song
        for song_id, song in _get_songs_from_song_ids(
            catalog, song_ids, song_filters
        ).items()
        if _check_meets_artists_requirements(
            catalog, song, credit_targets, group_granularity, max_other_artist
        )
    }

    return _format_songs(catalog, _select_songs(songs, ignore_duplicate))


def get_composer_ids_song_list(
    catalog: Catalog,
    composer_ids: list[int],
    arrangement: bool,
    group_granularity: int,
    max_other_artist: int,
    ignore_duplicate: bool,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """Songs credited to explicit composer/arranger IDs (and their groups)."""
    if not composer_ids:
        return []

    song_ids = catalog.song_ids_for_composers(
        _expand_search_artist_ids(catalog, composer_ids, group_granularity),
        arrangement,
    )

    credit_targets = _build_composer_credit_targets(catalog, composer_ids)

    songs = {
        song_id: song
        for song_id, song in _get_songs_from_song_ids(
            catalog, song_ids, song_filters
        ).items()
        if _check_meets_composers_requirements(
            catalog, song, credit_targets, arrangement, group_granularity, max_other_artist
        )
    }

    return _format_songs(catalog, _select_songs(songs, ignore_duplicate))


def get_ann_ids_song_list(
    catalog: Catalog,
    ann_ids: list[int],
    ignore_duplicate: bool,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """All songs for one or more Anime News Network anime IDs."""
    if not ann_ids:
        return []

    songs = catalog.songs_for_external_ids(
        ann_ids, catalog.songs_by_ann_id, song_filters
    )
    return _format_songs(catalog, _select_songs(songs, ignore_duplicate))


def get_mal_ids_song_list(
    catalog: Catalog,
    mal_ids: list[int],
    ignore_duplicate: bool,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """All songs linked to MyAnimeList anime IDs."""
    if not mal_ids:
        return []

    songs = catalog.songs_for_external_ids(
        mal_ids, catalog.songs_by_mal_id, song_filters
    )
    return _format_songs(catalog, _select_songs(songs, ignore_duplicate))


def get_ann_song_ids_song_list(
    catalog: Catalog,
    ann_song_ids: list[int],
    ignore_duplicate: bool,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """Fetch specific songs by Anime News Network song IDs."""
    if not ann_song_ids:
        return []

    songs = catalog.songs_for_external_ids(
        ann_song_ids, catalog.songs_by_ann_song_id, song_filters
    )
    return _format_songs(catalog, _select_songs(songs, ignore_duplicate))


def get_amq_song_ids_song_list(
    catalog: Catalog,
    amq_song_ids: list[int],
    ignore_duplicate: bool,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """Fetch specific songs by AMQ song IDs."""
    if not amq_song_ids:
        return []

    songs = catalog.songs_for_external_ids(
        amq_song_ids, catalog.songs_by_amq_song_id, song_filters
    )
    return _format_songs(catalog, _select_songs(songs, ignore_duplicate))


def get_season_song_list(
    catalog: Catalog,
    season: str,
    ignore_duplicate: bool,
    song_filters: SongFilters,
) -> list[FormattedSong]:
    """All songs from a season label (e.g. 'Winter 2020')."""
    songs = catalog.season_songs(season, song_filters)
    return _format_songs(catalog, _select_songs(songs, ignore_duplicate))
