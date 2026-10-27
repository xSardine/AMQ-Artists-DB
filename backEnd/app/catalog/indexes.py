"""Build immutable catalog indexes and autocomplete values from decoded records."""

from collections import defaultdict
from collections.abc import Sequence
from types import MappingProxyType

from catalog.credits import CreditGraph
from catalog.models import (
    AnimeCatalogEntry,
    AnimeLabelsByAnnId,
    ArtistDatabase,
    Catalog,
    LabelCanonicalMap,
    SearchName,
    Song,
    SongIdReverseMap,
    SongRowsByExternalId,
)


def _index_anime_labels(
    rows: Sequence[tuple[int, str | None]],
) -> tuple[AnimeLabelsByAnnId, LabelCanonicalMap]:
    """Group (annId, label) rows into per-anime sets and a canonical name map."""
    by_ann: dict[int, set[str]] = {}
    by_lower: dict[str, str] = {}
    for ann_id, label in rows:
        if not label:
            continue
        by_ann.setdefault(ann_id, set()).add(label)
        by_lower.setdefault(label.lower(), label)
    return {ann_id: frozenset(labels) for ann_id, labels in by_ann.items()}, by_lower


def _index_positive_id(
    rows_by_id: defaultdict[int, list[Song]],
    external_id: int | None,
    song: Song,
) -> None:
    """Index a list-site ID, skipping nulls and non-positive placeholders such as AniDB -1."""
    if external_id is not None and external_id > 0:
        rows_by_id[external_id].append(song)


def _freeze_row_map(
    rows: defaultdict[int, list[Song]],
) -> SongRowsByExternalId:
    return MappingProxyType({external_id: tuple(songs) for external_id, songs in rows.items()})


def _freeze_reverse_map(rows: defaultdict[int, list[int]]) -> SongIdReverseMap:
    return MappingProxyType({person_id: tuple(song_ids) for person_id, song_ids in rows.items()})


def _search_names(*values: str | None) -> tuple[SearchName, ...]:
    """Prepare distinct spellings once without collapsing case-sensitive aliases."""
    return tuple(SearchName(value, value.lower()) for value in dict.fromkeys(values) if value)


def build_catalog(
    song_rows: tuple[Song, ...],
    artists_by_id: ArtistDatabase,
    genre_rows: Sequence[tuple[int, str | None]],
    tag_rows: Sequence[tuple[int, str | None]],
    *,
    database_updated_at: str | None = None,
) -> Catalog:
    """Build lookup maps without changing source order or external-ID placeholder rules."""
    artists_by_id = MappingProxyType(dict(artists_by_id))
    genres_by_ann_id, genre_by_lower = _index_anime_labels(genre_rows)
    tags_by_ann_id, tag_by_lower = _index_anime_labels(tag_rows)

    songs_by_id: dict[int, Song] = {}
    songs_by_artist: defaultdict[int, list[int]] = defaultdict(list)
    songs_by_composer: defaultdict[int, list[int]] = defaultdict(list)
    songs_by_arranger: defaultdict[int, list[int]] = defaultdict(list)
    songs_by_ann: defaultdict[int, list[Song]] = defaultdict(list)
    songs_by_mal: defaultdict[int, list[Song]] = defaultdict(list)
    songs_by_anilist: defaultdict[int, list[Song]] = defaultdict(list)
    songs_by_kitsu: defaultdict[int, list[Song]] = defaultdict(list)
    songs_by_anidb: defaultdict[int, list[Song]] = defaultdict(list)
    songs_by_ann_song: defaultdict[int, list[Song]] = defaultdict(list)
    songs_by_amq_song: defaultdict[int, list[Song]] = defaultdict(list)
    songs_by_season: defaultdict[str, list[Song]] = defaultdict(list)
    artist_autocomplete_values: dict[str, None] = {}
    song_name_autocomplete_values: dict[str, None] = {}

    for song in song_rows:
        song_id = song.song_id
        ann_id = song.ann_id
        songs_by_id[song_id] = song
        songs_by_ann[ann_id].append(song)
        if song.anime_vintage:
            songs_by_season[song.anime_vintage].append(song)
        if song.mal_id is not None:
            songs_by_mal[song.mal_id].append(song)
        _index_positive_id(songs_by_anilist, song.anilist_id, song)
        _index_positive_id(songs_by_kitsu, song.kitsu_id, song)
        _index_positive_id(songs_by_anidb, song.anidb_id, song)
        if song.ann_song_id is not None:
            songs_by_ann_song[song.ann_song_id].append(song)
        if song.amq_song_id is not None:
            songs_by_amq_song[song.amq_song_id].append(song)

        for credits, reverse_map in (
            (song.artists, songs_by_artist),
            (song.composers, songs_by_composer),
            (song.arrangers, songs_by_arranger),
        ):
            if credits:
                for person_id, _ in credits:
                    reverse_map[person_id].append(song_id)

        artist_autocomplete_values.setdefault(song.romaji_song_artist, None)
        song_name_autocomplete_values.setdefault(song.romaji_song_name, None)
    artist_name_rows = tuple(
        (artist_id, name)
        for artist_id, artist in artists_by_id.items()
        for name in _search_names(*artist.names, *artist.original_names)
    )
    anime_by_id = MappingProxyType(
        {
            ann_id: AnimeCatalogEntry(
                anime_jp_name=rows[0].anime_jp_name,
                anime_en_name=rows[0].anime_en_name,
                anime_alt_names=rows[0].romaji_alt_names,
                anime_vintage=rows[0].anime_vintage,
                anime_type=rows[0].anime_type,
                anime_category=rows[0].anime_category,
                songs=tuple(rows),
                search_names=_search_names(
                    rows[0].anime_jp_name,
                    rows[0].anime_en_name,
                    *rows[0].romaji_alt_names,
                    rows[0].original_jp_name,
                    *rows[0].original_alt_names,
                ),
            )
            for ann_id, rows in songs_by_ann.items()
        }
    )
    graph = CreditGraph(artists_by_id)
    graph.validate()
    return Catalog(
        database_updated_at=database_updated_at,
        credits=graph,
        song_rows=song_rows,
        songs_by_id=MappingProxyType(songs_by_id),
        anime_by_id=anime_by_id,
        artists_by_id=artists_by_id,
        artist_name_rows=artist_name_rows,
        songs_by_artist_id=_freeze_reverse_map(songs_by_artist),
        songs_by_composer_id=_freeze_reverse_map(songs_by_composer),
        songs_by_arranger_id=_freeze_reverse_map(songs_by_arranger),
        songs_by_ann_id=_freeze_row_map(songs_by_ann),
        songs_by_mal_id=_freeze_row_map(songs_by_mal),
        songs_by_anilist_id=_freeze_row_map(songs_by_anilist),
        songs_by_kitsu_id=_freeze_row_map(songs_by_kitsu),
        songs_by_anidb_id=_freeze_row_map(songs_by_anidb),
        songs_by_ann_song_id=_freeze_row_map(songs_by_ann_song),
        songs_by_amq_song_id=_freeze_row_map(songs_by_amq_song),
        songs_by_season=MappingProxyType(
            {season: tuple(rows) for season, rows in songs_by_season.items()}
        ),
        genres_by_ann_id=MappingProxyType(genres_by_ann_id),
        tags_by_ann_id=MappingProxyType(tags_by_ann_id),
        genre_by_lower=MappingProxyType(genre_by_lower),
        tag_by_lower=MappingProxyType(tag_by_lower),
        artist_autocomplete_values=tuple(
            SearchName(value, value.lower())
            for value in sorted(artist_autocomplete_values, key=str.lower)
        ),
        song_name_autocomplete_values=tuple(
            SearchName(value, value.lower())
            for value in sorted(song_name_autocomplete_values, key=len)
        ),
    )
