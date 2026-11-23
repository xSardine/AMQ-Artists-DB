"""Summarize artist identities, aliases, group rosters, and song credit usage."""

from collections import Counter, defaultdict
from typing import TypedDict

from catalog.classification import normalize_song_category
from catalog.models import ArtistDatabase, Catalog, CreditPair


CREDIT_ROLES = {
    "performer": ("artists", "romaji_song_artist"),
    "composer": ("composers", "romaji_song_composer"),
    "arranger": ("arrangers", "romaji_song_arranger"),
}


class CreditGap(TypedDict):
    text_without_ids: int
    no_text_or_ids: int


class CreditRoleStatistics(TypedDict):
    songs_with_ids: int
    text_without_ids: int
    no_text_or_ids: int
    unique_direct_ids: int
    direct_people: int
    lineup_only_people: int
    all_identified_people: int
    specific_group_lineup_songs: int
    unspecified_group_lineup_songs: int
    songs_by_id_count: dict[str, int]
    missing_ids_by_performance: dict[str, CreditGap]


class GroupStatistics(TypedDict):
    total: int
    by_lineup_type: dict[str, int]
    by_lineup_count: dict[str, int]
    lineups_by_type: dict[str, int]
    nested_groups: int


class CreditedArtist(TypedDict):
    id: int
    name: str
    type: str | None
    disambiguation: str | None
    unique_songs: int
    anime_count: int


class ArtistCreditStatistics(TypedDict):
    types: dict[str, int]
    directly_credited: int
    roster_only: int
    other_catalog_entries: int
    role_combinations: dict[str, int]
    aliases: dict[str, int]
    groups: GroupStatistics
    roles: dict[str, CreditRoleStatistics]
    artists_by_unique_song_count: dict[str, int]
    most_credited: dict[str, list[CreditedArtist]]


def _bucket_counts(counts: Counter[int], bounds: tuple[int, ...]) -> dict[str, int]:
    """Partition a count distribution into inclusive ranges and a final open range."""
    buckets = {}
    start = 0
    for end in bounds:
        label = str(start) if start == end else f"{start}–{end}"
        buckets[label] = sum(count for value, count in counts.items() if start <= value <= end)
        start = end + 1
    buckets[f"{start}+"] = sum(count for value, count in counts.items() if value >= start)
    return buckets


def _alias_statistics(artists: ArtistDatabase) -> dict[str, int]:
    """Count regular aliases; shared-name comparisons ignore case, not identity."""
    ids_by_name: defaultdict[str, set[int]] = defaultdict(set)
    alias_counts: Counter[int] = Counter()
    for artist_id, artist in artists.items():
        names = {name.strip() for name in artist.names if name and name.strip()}
        alias_counts[len(names)] += 1
        for name in names:
            ids_by_name[name.casefold()].add(artist_id)
    shared_ids = set()
    shared_names = 0
    for ids in ids_by_name.values():
        if len(ids) > 1:
            shared_names += 1
            shared_ids.update(ids)
    return {
        "total_aliases": sum(size * count for size, count in alias_counts.items()),
        "distinct_names": len(ids_by_name),
        "artists_with_multiple_aliases": sum(
            count for size, count in alias_counts.items() if size > 1
        ),
        "shared_names": shared_names,
        "artists_with_shared_names": len(shared_ids),
        "artists_with_disambiguation": sum(
            bool(artist.disambiguation and artist.disambiguation.strip())
            for artist in artists.values()
        ),
    }


def _group_statistics(artists: ArtistDatabase) -> GroupStatistics:
    """Describe groups and choirs without treating people as groups."""
    groups = {artist_id: artist for artist_id, artist in artists.items() if artist.type != "person"}
    profiles = dict.fromkeys(("Vocalists only", "Composers only", "Both", "No lineups"), 0)
    lineup_types = dict.fromkeys(("Vocalists", "Composers"), 0)
    nested_groups = 0
    for artist in groups.values():
        kinds = {lineup.line_up_type for lineup in artist.line_ups}
        if not kinds:
            profile = "No lineups"
        elif kinds == {"vocalists"}:
            profile = "Vocalists only"
        elif kinds == {"composers"}:
            profile = "Composers only"
        else:
            profile = "Both"
        profiles[profile] += 1
        nested_groups += any(
            member_id in groups for lineup in artist.line_ups for member_id, _ in lineup.members
        )
        for lineup in artist.line_ups:
            lineup_types[lineup.line_up_type.title()] += 1
    return {
        "total": len(groups),
        "by_lineup_type": profiles,
        "by_lineup_count": _bucket_counts(
            Counter(len(artist.line_ups) for artist in groups.values()), (0, 1, 2, 5)
        ),
        "lineups_by_type": lineup_types,
        "nested_groups": nested_groups,
    }


def _people_in_lineups(catalog: Catalog, credits: set[CreditPair]) -> set[int]:
    """Resolve only explicitly credited lineups, reusing the catalog's roster caches."""
    people = set()
    for artist_id, lineup in credits:
        artist = catalog.artists_by_id.get(artist_id)
        if artist is None or not 0 <= lineup < len(artist.line_ups):
            continue
        for member_id in catalog.credits.flatten(artist.line_ups[lineup].members):
            member = catalog.artists_by_id.get(member_id)
            if member is not None and member.type == "person":
                people.add(member_id)
    return people


def _artist_name(artists: ArtistDatabase, artist_id: int) -> str:
    artist = artists.get(artist_id)
    return artist.names[0] if artist is not None and artist.names else str(artist_id)


def _most_credited(
    catalog: Catalog, role: str, songs_by_artist: dict[int, set[int]]
) -> list[CreditedArtist]:
    """Rank direct credits by distinct positive AMQ song IDs; count anime for the top ten."""
    ordered_ids = sorted(
        (artist_id for artist_id, songs in songs_by_artist.items() if songs),
        key=lambda artist_id: (
            -len(songs_by_artist[artist_id]),
            _artist_name(catalog.artists_by_id, artist_id).casefold(),
            artist_id,
        ),
    )[:10]
    anime_by_artist: dict[int, set[int]] = {artist_id: set() for artist_id in ordered_ids}
    fields = (
        [fields[0] for fields in CREDIT_ROLES.values()]
        if role == "all"
        else [CREDIT_ROLES[role][0]]
    )
    for song in catalog.song_rows:
        for field in fields:
            for artist_id, _ in getattr(song, field):
                if artist_id in anime_by_artist:
                    anime_by_artist[artist_id].add(song.ann_id)
    ranking: list[CreditedArtist] = []
    for artist_id in ordered_ids:
        artist = catalog.artists_by_id.get(artist_id)
        ranking.append(
            {
                "id": artist_id,
                "name": _artist_name(catalog.artists_by_id, artist_id),
                "type": artist.type if artist is not None else None,
                "disambiguation": artist.disambiguation if artist is not None else None,
                "unique_songs": len(songs_by_artist[artist_id]),
                "anime_count": len(anime_by_artist[artist_id]),
            }
        )
    return ranking


def build_artist_credit_statistics(catalog: Catalog) -> ArtistCreditStatistics:
    """Aggregate direct IDs, resolved people, missing credit context, and song reach."""
    artists = catalog.artists_by_id
    roles: dict[str, CreditRoleStatistics] = {}
    role_ids: dict[str, set[int]] = {}
    all_songs_by_artist: defaultdict[int, set[int]] = defaultdict(set)
    most_credited: dict[str, list[CreditedArtist]] = {}
    for role, (field, text_field) in CREDIT_ROLES.items():
        pairs: set[CreditPair] = set()
        credit_sizes: Counter[int] = Counter()
        gaps: dict[str, CreditGap] = {}
        songs_by_artist: defaultdict[int, set[int]] = defaultdict(set)
        with_ids = text_only = empty = specific = unspecified = 0
        for song in catalog.song_rows:
            credits = getattr(song, field)
            ids = {artist_id for artist_id, _ in credits}
            credit_sizes[len(ids)] += 1
            pairs.update(credits)
            if credits:
                with_ids += 1
            else:
                text = getattr(song, text_field)
                has_text = bool(text and text.strip())
                text_only += has_text
                empty += not has_text
                performance = normalize_song_category(song.song_category)
                gap = gaps.setdefault(performance, {"text_without_ids": 0, "no_text_or_ids": 0})
                gap["text_without_ids" if has_text else "no_text_or_ids"] += 1
            group_credits = [
                lineup
                for artist_id, lineup in credits
                if artist_id in artists and artists[artist_id].type != "person"
            ]
            specific += any(lineup >= 0 for lineup in group_credits)
            unspecified += -1 in group_credits
            for artist_id in ids:
                own_songs = songs_by_artist[artist_id]
                all_songs = all_songs_by_artist[artist_id]
                if song.amq_song_id is not None and song.amq_song_id > 0:
                    own_songs.add(song.amq_song_id)
                    all_songs.add(song.amq_song_id)
        direct_ids = set(songs_by_artist)
        direct_people = {
            artist_id
            for artist_id in direct_ids
            if artist_id in artists and artists[artist_id].type == "person"
        }
        lineup_people = _people_in_lineups(catalog, pairs)
        roles[role] = {
            "songs_with_ids": with_ids,
            "text_without_ids": text_only,
            "no_text_or_ids": empty,
            "unique_direct_ids": len(direct_ids),
            "direct_people": len(direct_people),
            "lineup_only_people": len(lineup_people - direct_people),
            "all_identified_people": len(direct_people | lineup_people),
            "specific_group_lineup_songs": specific,
            "unspecified_group_lineup_songs": unspecified,
            "songs_by_id_count": _bucket_counts(credit_sizes, (0, 1, 2, 5)),
            "missing_ids_by_performance": dict(sorted(gaps.items())),
        }
        role_ids[role] = direct_ids
        most_credited[role] = _most_credited(catalog, role, songs_by_artist)
    credited = set(all_songs_by_artist)
    known_credited = credited & artists.keys()
    roster_ids = {
        member_id
        for artist in artists.values()
        for lineup in artist.line_ups
        for member_id, _ in lineup.members
    } & artists.keys()
    role_combinations: Counter[str] = Counter()
    for artist_id in credited:
        combination = " + ".join(role.title() for role, ids in role_ids.items() if artist_id in ids)
        role_combinations[combination] += 1
    most_credited["all"] = _most_credited(catalog, "all", all_songs_by_artist)
    return {
        "types": {
            kind.title(): sum(artist.type == kind for artist in artists.values())
            for kind in ("person", "group", "choir")
        },
        "directly_credited": len(known_credited),
        "roster_only": len(roster_ids - known_credited),
        "other_catalog_entries": len(artists.keys() - known_credited - roster_ids),
        "role_combinations": dict(
            sorted(role_combinations.items(), key=lambda item: (-item[1], item[0]))
        ),
        "aliases": _alias_statistics(artists),
        "groups": _group_statistics(artists),
        "roles": roles,
        "artists_by_unique_song_count": _bucket_counts(
            Counter(len(songs) for songs in all_songs_by_artist.values()), (0, 1, 5, 20, 100)
        ),
        "most_credited": most_credited,
    }
