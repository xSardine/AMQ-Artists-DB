import utils
import sql_calls
from itertools import chain
from typing import Any

from song_filters import SongFilters

FormattedSong = dict[str, Any]

# Groups with line-ups that also credit songs without a line-up.
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


def _song_id_set(songs) -> set:
    """Collect songs.id keys (songsFull.songId, column index 13) for AND-logic membership checks."""
    if not songs:
        return set()
    return {song[13] for song in songs}


def _append_formatted_song(
    artist_database,
    song,
    final_song_list,
    song_ids_done,
    duplicate_indexes,
    ignore_duplicate,
):
    """Add a formatted song, or replace an existing duplicate when ignore_duplicate keeps the lower annId."""
    duplicate_key = (song[20], song[22])
    duplicate_index = duplicate_indexes.get(duplicate_key, -1)

    if not ignore_duplicate or duplicate_index == -1:
        song_ids_done.add(song[13])
        duplicate_indexes[duplicate_key] = len(final_song_list)
        final_song_list.append(utils.format_song(artist_database, song))
        return

    if final_song_list[duplicate_index]["annId"] > song[0]:
        song_ids_done.add(song[13])
        final_song_list[duplicate_index] = utils.format_song(artist_database, song)


def _passes_and_logic(
    song,
    anime_search_filters,
    song_name_search_filters,
    artist_search_filters,
    composer_search_filters,
    anime_song_ids,
    song_name_song_ids,
    artist_song_ids,
    composer_song_ids,
):
    """AND mode: song must appear in every active filter's result set (by songs.id / songsFull.songId)."""
    if utils.has_search_text(artist_search_filters):
        if song[13] not in artist_song_ids:
            return False
    if utils.has_search_text(anime_search_filters):
        if song[13] not in anime_song_ids:
            return False
    if utils.has_search_text(song_name_search_filters):
        if song[13] not in song_name_song_ids:
            return False
    if utils.has_search_text(composer_search_filters):
        if song[13] not in composer_song_ids:
            return False
    return True


def combine_results(
    artist_database,
    anime_songs_list,
    song_name_songs_list=(),
    artist_songs_list=(),
    composer_songs_list=(),
    and_logic=False,
    ignore_duplicate=False,
    max_nb_songs=None,
    anime_search_filters=None,
    song_name_search_filters=None,
    artist_search_filters=None,
    composer_search_filters=None,
) -> list[FormattedSong]:
    """Merge per-filter raw song lists into formatted API entries.

    OR mode (default): union of all lists, deduped by songs.id (songsFull.songId).
    AND mode: only songs whose id appears in every active filter branch.
    ignore_duplicate: collapse same songName+songArtist, preferring the row with lower annId.
    """

    song_ids_done = set()
    duplicate_indexes = {}
    final_song_list = []
    if and_logic:
        anime_song_ids = _song_id_set(anime_songs_list)
        song_name_song_ids = _song_id_set(song_name_songs_list)
        artist_song_ids = _song_id_set(artist_songs_list)
        composer_song_ids = _song_id_set(composer_songs_list)

    for song in chain(
        anime_songs_list or (),
        song_name_songs_list or (),
        artist_songs_list or (),
        composer_songs_list or (),
    ):
        if max_nb_songs and len(final_song_list) >= max_nb_songs:
            break

        if song[13] in song_ids_done:
            continue

        if and_logic and not _passes_and_logic(
            song,
            anime_search_filters,
            song_name_search_filters,
            artist_search_filters,
            composer_search_filters,
            anime_song_ids,
            song_name_song_ids,
            artist_song_ids,
            composer_song_ids,
        ):
            continue

        _append_formatted_song(
            artist_database,
            song,
            final_song_list,
            song_ids_done,
            duplicate_indexes,
            ignore_duplicate,
        )

    return final_song_list


def _effective_partial_match(search_filter) -> bool:
    """Short queries (<=2 chars) force whole-string regex (^...$) even if partial_match is requested."""
    if len(search_filter.search) <= 2:
        return False
    return search_filter.partial_match


def _anime_names(anime) -> list[str]:
    """All searchable anime titles for one anime entry, including $-separated alt names."""
    names = [anime["animeJPName"], anime["animeENName"]]
    alt = anime.get("animeAltNames")
    if alt:
        names.extend(alt.split("\\$"))
    return names


def search_anime_songs(anime_database, filters: SongFilters, search_filter) -> list:
    """Regex-match anime JP/EN/alt names, return filtered songs from matching anime."""
    anime_search = utils.get_regex_search(
        search_filter.search,
        _effective_partial_match(search_filter),
        match_case=search_filter.match_case,
    )
    match_case = search_filter.match_case
    results = []
    for anime in anime_database.values():
        if not any(
            name and utils.regex_match(anime_search, name, match_case)
            for name in _anime_names(anime)
        ):
            continue
        for song in anime["songs"]:
            if filters.matches_row(song):
                results.append(song)
    return results


def search_song_name_songs(song_database, filters: SongFilters, search_filter) -> list:
    """Regex-match the song title field across the in-memory song database."""
    song_name_search = utils.get_regex_search(
        search_filter.search,
        _effective_partial_match(search_filter),
        match_case=search_filter.match_case,
    )
    match_case = search_filter.match_case
    results = []
    for song in song_database.values():
        if utils.regex_match(song_name_search, song[20], match_case) and filters.matches_row(song):
            results.append(song)
    return results


def get_member_list_flat(artist_database, artists, bottom=True) -> list[int]:
    """Flatten credited artists/groups into a list of individual performer IDs.

    artists: list of [artist_id, line_up_index] pairs from a song credit string.
    bottom=True: only count people inside line-ups, not the group ID on the credit.
    bottom=False: include the group ID too, then still expand nested line-up members.
    """
    member_list = []

    for artist, line_up in artists:
        if line_up == -1:
            member_list.append(int(artist))

        else:
            if not bottom:
                member_list.append(int(artist))

            artist_entry = artist_database.get(str(artist))
            if not artist_entry:
                continue
            line_ups = artist_entry["line_ups"]
            if line_up >= len(line_ups):
                continue

            for member in get_member_list_flat(
                artist_database,
                line_ups[line_up]["members"],
                bottom=bottom,
            ):
                member_list.append(int(member))

    return member_list


def compare_artist_overlap(song_artists, target_artists) -> tuple[int, int]:
    """Count shared artist IDs and extra song credits, ignoring credit order."""
    song_artists = set(song_artists)
    target_artists = set(target_artists)
    same_count = len(song_artists & target_artists)
    add_count = len(song_artists - target_artists)
    return same_count, add_count


def check_meets_artists_requirements(
    artist_database, song, artist_ids, group_granularity, max_other_artist
) -> bool:
    """True if the song's credited performers satisfy the artist search constraints.

    For each matched artist ID, try every vocalist line-up (plus solo credit for
    LINE_UP_EXCEPTIONS groups). Requires at least one overlapping member, at most
    max_other_artist extra performers on the song, and enough overlap per
    group_granularity (min overlapping flattened IDs: present_artist >= min(granularity, len(line_up))).
    """

    song_artists = [
        [artist, int(line_up)]
        for artist, line_up in zip(song[23].split(","), song[24].split(","))
    ]
    song_artists_flat = set(get_member_list_flat(artist_database, song_artists))

    for artist_id in artist_ids:
        line_ups = [[[str(artist_id), -1]]]

        artist = artist_database.get(str(artist_id))
        if not artist:
            continue

        if artist["line_ups"]:
            line_ups = [
                line_up["members"]
                for line_up in artist["line_ups"]
                if line_up["line_up_type"] == "vocalists"
            ]

            if artist_id in LINE_UP_EXCEPTIONS:
                line_ups += [[[str(artist_id), -1]]]

        for line_up in line_ups:
            checked_list = get_member_list_flat(artist_database, line_up)
            present_artist, additional_artist = compare_artist_overlap(
                song_artists_flat, checked_list
            )

            # At least one overlap, not too many extra song credits, and min overlap per group_granularity.
            if (
                present_artist >= 1
                and additional_artist <= max_other_artist
                and present_artist >= min(group_granularity, len(line_up))
            ):
                return True

    return False


def check_meets_composers_requirements(
    artist_database,
    song,
    composer_ids,
    group_granularity,
    max_other_artist,
    arrangement,
) -> bool:
    """True if the song's composer/arranger credits satisfy the composer search constraints.

    Mirrors check_meets_artists_requirements for composing-team credits, optionally
    including arranger credits when arrangement=True.
    """
    song_composers = []
    if song[27]:
        song_composers += [
            [artist, int(line_up)]
            for artist, line_up in zip(song[27].split(","), song[28].split(","))
        ]
    if arrangement and song[31]:
        song_composers += [
            [artist, int(line_up)]
            for artist, line_up in zip(song[31].split(","), song[32].split(","))
        ]
    song_artists_flat = set(get_member_list_flat(artist_database, song_composers))

    for composer_id in composer_ids:
        line_ups = [[[str(composer_id), -1]]]
        artist = artist_database.get(str(composer_id))
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
            line_ups += [[[str(composer_id), -1]]]

        for line_up in line_ups:
            checked_list = get_member_list_flat(artist_database, line_up)
            present_artist, additional_artist = compare_artist_overlap(
                song_artists_flat, checked_list
            )

            if (
                present_artist >= 1
                and additional_artist <= max_other_artist
                and present_artist >= min(group_granularity, len(line_up))
            ):
                return True

    return False


def get_songs_from_song_ids(song_database, song_ids, filters: SongFilters) -> list:
    """Look up songs.id keys in the in-memory song database; return raw songsFull rows, filtered."""
    song_list = []

    for song_id in song_ids:
        song = song_database.get(song_id)
        if song is not None and filters.matches_row(song):
            song_list.append(song)
   
    return song_list


def _expand_search_artist_ids(artist_database, root_ids, group_granularity):
    """Widen regex-matched artist IDs before SQL song lookup.

    Includes parent groups, and when group_granularity > 0 also expands line-up
    members so songs credited to sub-units are found.
    """
    members = []
    if group_granularity > 0:
        for artist in root_ids:
            artist_entry = artist_database.get(str(artist))
            if not artist_entry:
                continue
            if artist_entry["line_ups"]:
                for line_up in artist_entry["line_ups"]:
                    for member in get_member_list_flat(
                        artist_database, line_up["members"], bottom=False
                    ):
                        if member not in members:
                            members.append(member)
            else:
                members.append(artist)

    all_groups: list[tuple[int, int]] = []
    for artist in set(root_ids + members):
        all_groups.extend(get_all_groups(artist, artist_database))

    return list(set(root_ids + [group_id for group_id, _ in all_groups] + members))


def get_all_groups(artist_id, artist_database, include_composers_groups=False) -> list[tuple[int, int]]:
    """Recursively list every parent group (group_id, line_up) for an artist."""
    entry = artist_database.get(str(artist_id))
    if not entry:
        return []

    # TODO: The 'include_composers_groups' parameter is currently unused
    # Might be a problem in the long run to take into account composers groups
    groups: list[tuple[int, int]] = []
    for group in entry["groups"]:
        group_id, line_up = int(group[0]), int(group[1])
        groups.append((group_id, line_up))
        groups.extend(get_all_groups(group_id, artist_database, include_composers_groups))

    return groups


def process_artist(
    song_database,
    artist_database,
    search,
    partial_match,
    match_case,
    filters: SongFilters,
    group_granularity,
    max_other_artist,
) -> tuple[list, list[int]]:
    """Resolve artist name to IDs, widen to groups/members, fetch songs, filter by credit rules."""
    artist_search = utils.get_regex_search(
        search, partial_match, swap_words=True, match_case=match_case
    )

    artist_ids = sql_calls.get_artist_ids_from_regex(
        artist_search, match_case=match_case
    )

    # If no IDs found, fall back to REGEXP on romajiSongArtist
    if not artist_ids:
        artist_songs_list = sql_calls.get_song_list_from_songArtist(
            artist_search, filters, match_case=match_case
        )
        return artist_songs_list, artist_ids

    song_ids = sql_calls.get_song_ids_from_artist_ids(
        _expand_search_artist_ids(artist_database, artist_ids, group_granularity),
    )

    artist_songs_list = get_songs_from_song_ids(
        song_database, song_ids, filters
    )

    final_song_list = []
    for song in artist_songs_list:
        if check_meets_artists_requirements(
            artist_database, song, artist_ids, group_granularity, max_other_artist
        ):
            final_song_list.append(song)

    return final_song_list, artist_ids


def process_composer(
    song_database,
    artist_database,
    search,
    partial_match,
    match_case,
    arrangement,
    filters: SongFilters,
    group_granularity,
    max_other_artist,
) -> tuple[list, list[int]]:
    """Resolve composer name to IDs, widen to groups/members, fetch songs, filter by credit rules."""

    composer_search = utils.get_regex_search(
        search, partial_match, swap_words=True, match_case=match_case
    )

    composer_ids = sql_calls.get_artist_ids_from_regex(
        composer_search, match_case=match_case
    )

    # If no IDs found, skip romajiSongComposer fallback (unlike artist search; saves compute time).
    if not composer_ids:
        return [], []

    song_ids = sql_calls.get_song_ids_from_composing_team_ids(
        composer_ids=_expand_search_artist_ids(artist_database, composer_ids, group_granularity),
        arrangement=arrangement,
    )

    composer_songs_list = get_songs_from_song_ids(
        song_database, song_ids, filters
    )

    final_song_list = []
    for song in composer_songs_list:
        if check_meets_composers_requirements(
            artist_database, song, composer_ids, group_granularity, max_other_artist, arrangement
        ):
            final_song_list.append(song)

    return final_song_list, composer_ids


def get_search_results(
    anime_search_filters,
    song_name_search_filters,
    artist_search_filters,
    composer_search_filters,
    and_logic,
    ignore_duplicate,
    max_nb_songs,
    filters: SongFilters,
) -> list[FormattedSong]:
    """Main /api/search_request pipeline: run each active text filter, then merge results."""
    artist_database = sql_calls.extract_artist_database()

    anime_songs_list = []
    if utils.has_search_text(anime_search_filters):
        anime_database = sql_calls.extract_anime_database()
        anime_songs_list = search_anime_songs(anime_database, filters, anime_search_filters)

    song_name_songs_list = []
    artist_songs_list = []
    composer_songs_list = []

    # Song DB is large; only load when a filter scans individual songs or artist/composer paths need it.
    needs_song_database = bool(
        utils.has_search_text(song_name_search_filters)
        or utils.has_search_text(artist_search_filters)
        or utils.has_search_text(composer_search_filters)
    )
    song_database = sql_calls.extract_song_database() if needs_song_database else None

    if utils.has_search_text(song_name_search_filters):
        song_name_songs_list = search_song_name_songs(
            song_database, filters, song_name_search_filters
        )

    if utils.has_search_text(artist_search_filters):
        artist_songs_list, _ = process_artist(
            song_database,
            artist_database,
            artist_search_filters.search,
            _effective_partial_match(artist_search_filters),
            artist_search_filters.match_case,
            filters,
            artist_search_filters.group_granularity,
            artist_search_filters.max_other_artist,
        )

    if utils.has_search_text(composer_search_filters):
        composer_songs_list, _ = process_composer(
            song_database,
            artist_database,
            composer_search_filters.search,
            _effective_partial_match(composer_search_filters),
            composer_search_filters.match_case,
            composer_search_filters.arrangement,
            filters,
            composer_search_filters.group_granularity,
            composer_search_filters.max_other_artist,
        )

    return combine_results(
        artist_database,
        anime_songs_list,
        song_name_songs_list,
        artist_songs_list,
        composer_songs_list,
        and_logic,
        ignore_duplicate,
        max_nb_songs,
        anime_search_filters,
        song_name_search_filters,
        artist_search_filters,
        composer_search_filters,
    )


def get_artist_ids_song_list(
    artist_ids,
    max_other_artist,
    group_granularity,
    ignore_duplicate,
    filters: SongFilters,
) -> list[FormattedSong]:
    """Songs credited to explicit artist IDs (and their groups), without name-regex search.
    Uses group_granularity and max_other_artist the same way as artist name search.
    """
    if not artist_ids:
        return []

    artist_database = sql_calls.extract_artist_database()

    song_ids = sql_calls.get_song_ids_from_artist_ids(
        _expand_search_artist_ids(artist_database, artist_ids, group_granularity),
    )

    song_database = sql_calls.extract_song_database()
    songs = get_songs_from_song_ids(song_database, song_ids, filters)
    final_songs = [
        song
        for song in songs
        if check_meets_artists_requirements(
            artist_database, song, artist_ids, group_granularity, max_other_artist
        )
    ]

    return combine_results(artist_database, final_songs, ignore_duplicate=ignore_duplicate)


def get_composer_ids_song_list(
    composer_ids,
    arrangement,
    group_granularity,
    max_other_artist,
    ignore_duplicate,
    filters: SongFilters,
) -> list[FormattedSong]:
    """Songs credited to explicit composer/arranger IDs (and their groups)."""
    if not composer_ids:
        return []

    artist_database = sql_calls.extract_artist_database()

    song_ids = sql_calls.get_song_ids_from_composing_team_ids(
        _expand_search_artist_ids(artist_database, composer_ids, group_granularity),
        arrangement=arrangement,
    )

    song_database = sql_calls.extract_song_database()
    songs = get_songs_from_song_ids(song_database, song_ids, filters)
    final_songs = [
        song
        for song in songs
        if check_meets_composers_requirements(
            artist_database, song, composer_ids, group_granularity, max_other_artist, arrangement
        )
    ]

    return combine_results(artist_database, final_songs, ignore_duplicate=ignore_duplicate)


def get_ann_ids_song_list(
    ann_ids,
    ignore_duplicate,
    filters: SongFilters,
) -> list[FormattedSong]:
    """All songs for one or more Anime News Network anime IDs."""
    if not ann_ids:
        return []

    artist_database = sql_calls.extract_artist_database()
    songs = sql_calls.get_songs_list_from_ann_ids(ann_ids, filters)
    return combine_results(artist_database, songs, ignore_duplicate=ignore_duplicate)


def get_mal_ids_song_list(
    mal_ids,
    ignore_duplicate,
    filters: SongFilters,
) -> list[FormattedSong]:
    """All songs linked to MyAnimeList anime IDs."""
    if not mal_ids:
        return []

    artist_database = sql_calls.extract_artist_database()
    songs = sql_calls.get_songs_list_from_mal_ids(mal_ids, filters)
    return combine_results(artist_database, songs, ignore_duplicate=ignore_duplicate)


def get_ann_song_ids_song_list(
    ann_song_ids,
    ignore_duplicate,
    filters: SongFilters,
) -> list[FormattedSong]:
    """Fetch specific songs by Anime News Network song IDs."""
    if not ann_song_ids:
        return []

    artist_database = sql_calls.extract_artist_database()
    songs = sql_calls.get_songs_list_from_ann_song_ids(ann_song_ids, filters)
    return combine_results(artist_database, songs, ignore_duplicate=ignore_duplicate)


def get_amq_song_ids_song_list(
    amq_song_ids,
    ignore_duplicate,
    filters: SongFilters,
) -> list[FormattedSong]:
    """Fetch specific songs by AMQ song IDs."""
    if not amq_song_ids:
        return []

    artist_database = sql_calls.extract_artist_database()
    songs = sql_calls.get_songs_list_from_amq_song_ids(amq_song_ids, filters)
    return combine_results(artist_database, songs, ignore_duplicate=ignore_duplicate)


def get_season_song_list(
    season,
    ignore_duplicate,
    filters: SongFilters,
) -> list[FormattedSong]:
    """All songs from a season label (e.g. 'Winter 2020')."""
    artist_database = sql_calls.extract_artist_database()
    songs = sql_calls.get_songs_list_from_season(season, filters)
    return combine_results(artist_database, songs, ignore_duplicate=ignore_duplicate)
