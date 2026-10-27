"""Performer and composer credit policies shared by name and ID searches."""

from collections.abc import Sequence
from typing import NamedTuple

from catalog.models import Catalog, CreditPair, Credits, Song
from search.models import IdMatch


class CreditTarget(NamedTuple):
    """One search-side roster used for artist/composer overlap checks."""

    # Distinct artist IDs after recursively expanding nested group lineups.
    # Used to check credit overlap and cap the required member count, so nested
    # subgroups do not count as single members. Direct credits remain unexpanded.
    members_flat: frozenset[int]


CreditTargetGroups = list[list[CreditTarget]]


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


def build_artist_credit_targets(
    catalog: Catalog,
    artist_ids: Sequence[int],
) -> CreditTargetGroups:
    """Keep each requested artist's alternative vocalist line-ups together."""
    targets: CreditTargetGroups = []

    for artist_id in dict.fromkeys(artist_ids):
        line_ups: list[Credits] = [((artist_id, -1),)]
        artist = catalog.artists_by_id.get(artist_id)
        if not artist:
            targets.append([])
            continue

        if artist.line_ups:
            line_ups = [
                line_up.members
                for line_up in artist.line_ups
                if line_up.line_up_type == "vocalists"
            ]
            if artist_id in LINE_UP_EXCEPTIONS:
                line_ups.append(((artist_id, -1),))

        targets.append([CreditTarget(catalog.credits.flatten(line_up)) for line_up in line_ups])

    return targets


def build_composer_credit_targets(
    catalog: Catalog,
    composer_ids: Sequence[int],
) -> CreditTargetGroups:
    """Keep each requested composer's alternative line-ups together."""

    # TODO: Composer and arranger searches currently consider every group line-up.
    # Ideally they should use only line-ups whose type is `composers`, but many
    # legacy groups have composer/arranger credits without a composer-specific
    # roster. Filtering strictly would make those groups stop expanding to their
    # members. Prefer composer line-ups when available and retain vocalist line-ups
    # only as a fallback until the source data has been fully curated.

    targets: CreditTargetGroups = []

    for composer_id in dict.fromkeys(composer_ids):
        line_ups: list[Credits] = [((composer_id, -1),)]
        artist = catalog.artists_by_id.get(composer_id)
        if not artist:
            targets.append([])
            continue

        if artist.line_ups:
            line_ups = [line_up.members for line_up in artist.line_ups]
            line_ups.append(((composer_id, -1),))

        targets.append([CreditTarget(catalog.credits.flatten(line_up)) for line_up in line_ups])

    return targets


def _credits_match_targets(
    song_credits_flat: frozenset[int],
    credit_targets: CreditTargetGroups,
    group_granularity: int,
    max_other_artist: int,
    id_match: IdMatch = "any",
) -> bool:
    """Preserve per-target extra-person limits for OR; combine selected matches for AND."""
    if id_match == "all":
        return _credits_match_all_targets(
            song_credits_flat, credit_targets, group_granularity, max_other_artist
        )

    for group in credit_targets:
        for target in group:
            present_artist = len(song_credits_flat & target.members_flat)
            if present_artist < 1:
                continue
            additional_artist = len(song_credits_flat - target.members_flat)
            if (
                additional_artist <= max_other_artist
                # Nested subgroups must not lower a threshold measured in people.
                and present_artist >= min(group_granularity, len(target.members_flat))
            ):
                return True

    return False


def _credits_match_all_targets(
    song_credits_flat: frozenset[int],
    target_groups: CreditTargetGroups,
    group_granularity: int,
    max_other_artist: int,
) -> bool:
    """Match every requested ID, choosing one qualifying line-up per ID."""
    if not target_groups:
        return False

    covered: frozenset[int] = frozenset()
    choices: list[list[frozenset[int]]] = []
    for targets in target_groups:
        overlaps: set[frozenset[int]] = set()
        for target in targets:
            overlap = song_credits_flat & target.members_flat
            if overlap and len(overlap) >= min(group_granularity, len(target.members_flat)):
                overlaps.add(overlap)
        if not overlaps:
            return False

        # A smaller qualifying roster cannot cover more of this song's people.
        maximal = [
            overlap
            for overlap in overlaps
            if not any(overlap < other for other in overlaps)
        ]
        if len(maximal) == 1:
            covered |= maximal[0]
        else:
            choices.append(sorted(maximal, key=len, reverse=True))

    # All IDs qualify. Only ambiguous historical line-ups need a combination search.
    choices.sort(key=len)
    remaining = [frozenset() for _ in range(len(choices) + 1)]
    for index in reversed(range(len(choices))):
        remaining[index] = remaining[index + 1].union(*choices[index])

    pending = [(0, covered)]
    seen: set[tuple[int, frozenset[int]]] = set()
    while pending:
        index, matched = pending.pop()
        if (index, matched) in seen:
            continue
        seen.add((index, matched))
        if len(song_credits_flat - matched) <= max_other_artist:
            return True
        if (
            index == len(choices)
            or len(song_credits_flat - matched - remaining[index]) > max_other_artist
        ):
            continue
        pending.extend((index + 1, matched | roster) for roster in reversed(choices[index]))

    return False


def check_meets_artists_requirements(
    catalog: Catalog,
    song: Song,
    credit_targets: CreditTargetGroups,
    group_granularity: int,
    max_other_artist: int,
    id_match: IdMatch = "any",
) -> bool:
    """True if the song's credited performers satisfy the artist search constraints."""
    return _credits_match_targets(
        catalog.credits.flatten(song.artists),
        credit_targets,
        group_granularity,
        max_other_artist,
        id_match,
    )


def check_meets_composers_requirements(
    catalog: Catalog,
    song: Song,
    credit_targets: CreditTargetGroups,
    arrangement: bool,
    group_granularity: int,
    max_other_artist: int,
    id_match: IdMatch = "any",
) -> bool:
    """True if the song's composer/arranger credits satisfy the composer search constraints."""
    song_composers: list[CreditPair] = []
    if song.composers:
        song_composers.extend(song.composers)
    if arrangement and song.arrangers:
        song_composers.extend(song.arrangers)

    return _credits_match_targets(
        catalog.credits.flatten(tuple(song_composers)),
        credit_targets,
        group_granularity,
        max_other_artist,
        id_match,
    )


def expand_search_artist_ids(
    catalog: Catalog,
    root_ids: Sequence[int],
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
            artist_entry = catalog.artists_by_id.get(artist_id)
            if artist_entry:
                for line_up in artist_entry.line_ups:
                    line_up_member_ids.update(catalog.credits.flatten(line_up.members, False))

    parent_group_ids = {
        group_id
        for artist_id in root_id_set | line_up_member_ids
        for group_id, _ in catalog.credits.parent_groups(artist_id)
    }

    return list(root_id_set | line_up_member_ids | parent_group_ids)
