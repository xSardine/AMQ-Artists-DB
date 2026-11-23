"""Translate validated API requests into search criteria and catalog filter values."""

from fastapi import HTTPException

from api import schemas
from catalog.models import Catalog, LabelCanonicalMap
from search import models as internal
from search.filters import LabelSetRequirements, MediaLinksRequirements, SongFilters

SONG_TYPE_IDS = {
    "opening": 1,
    "ending": 2,
    "insert": 3,
}
BROADCAST_NAMES = {
    "normal": "Normal",
    "dub": "Dub",
    "rebroadcast": "Rebroadcast",
}
CATEGORY_NAMES = {
    "standard": "Standard",
    "character": "Character",
    "chanting": "Chanting",
    "instrumental": "Instrumental",
    "other": "Other",
}
ANIME_TYPE_NAMES = {
    "tv": "TV",
    "movie": "Movie",
    "ova": "OVA",
    "ona": "ONA",
    "special": "Special",
    "other": "Other",
}


# Resolve validated API filter values to the database values used by SongFilters.
def resolve_song_filters(query: schemas.FilteredRequest, catalog: Catalog) -> SongFilters:
    filters = query.filters

    return SongFilters(
        song_types=frozenset(SONG_TYPE_IDS[value] for value in filters.song_types),
        broadcasts=frozenset(BROADCAST_NAMES[value] for value in filters.broadcasts),
        song_categories=frozenset(CATEGORY_NAMES[value] for value in filters.song_categories),
        anime_types=frozenset(ANIME_TYPE_NAMES[value] for value in filters.anime_types),
        season_start=filters.season.start if filters.season else None,
        season_end=filters.season.end if filters.season else None,
        difficulty_start=filters.difficulty.start if filters.difficulty else None,
        difficulty_end=filters.difficulty.end if filters.difficulty else None,
        include_no_difficulty=(
            filters.difficulty.include_no_difficulty if filters.difficulty is not None else False
        ),
        song_length_start=filters.song_length.start if filters.song_length else None,
        song_length_end=filters.song_length.end if filters.song_length else None,
        include_no_length=(
            filters.song_length.include_no_length if filters.song_length is not None else False
        ),
        media_links=(
            MediaLinksRequirements(
                require_any=frozenset(filters.media_links.require_any),
                require_all=frozenset(filters.media_links.require_all),
                exclude=frozenset(filters.media_links.exclude),
            )
            if filters.media_links is not None
            else None
        ),
        genres=_resolve_label_set_requirements(filters.genres, catalog.genre_by_lower, "genre"),
        tags=_resolve_label_set_requirements(filters.tags, catalog.tag_by_lower, "tag"),
        genres_by_ann_id=catalog.genres_by_ann_id,
        tags_by_ann_id=catalog.tags_by_ann_id,
    )


def _resolve_label_set_requirements(
    label_filter: schemas.AnimeLabelsFilter | None,
    by_lower: LabelCanonicalMap,
    kind: str,
) -> LabelSetRequirements | None:
    """Canonicalize genre/tag names against the catalog; reject unknowns with 422."""
    if label_filter is None:
        return None

    requirements = LabelSetRequirements(
        require_any=_canonicalize_labels(label_filter.require_any, by_lower, kind),
        require_all=_canonicalize_labels(label_filter.require_all, by_lower, kind),
        exclude=_canonicalize_labels(label_filter.exclude, by_lower, kind),
    )
    try:
        schemas.validate_requirements(
            requirements.require_any, requirements.require_all, requirements.exclude, kind
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return requirements


def _canonicalize_labels(
    values: list[str],
    by_lower: LabelCanonicalMap,
    kind: str,
) -> frozenset[str]:
    canonical: list[str] = []
    unknown: list[str] = []
    for value in values:
        resolved = by_lower.get(value.lower())
        if resolved is None:
            unknown.append(value)
        else:
            canonical.append(resolved)
    if unknown:
        unknown_list = ", ".join(repr(label) for label in unknown)
        raise HTTPException(
            status_code=422,
            detail=f"Unknown {kind}(s): {unknown_list}.",
        )
    return frozenset(canonical)


def to_search_query(query: schemas.SongSelectionRequest, catalog: Catalog) -> internal.SearchQuery:
    """Translate every validated API operation into one internal search request."""
    criteria: internal.SearchCriteria
    limit = None
    match query:
        case schemas.SearchRequest():
            criteria = internal.TextCriteria(
                anime=(
                    internal.TextSearchFilter(**query.anime_search_filter.model_dump())
                    if query.anime_search_filter is not None
                    else None
                ),
                song_name=(
                    internal.TextSearchFilter(**query.song_name_search_filter.model_dump())
                    if query.song_name_search_filter is not None
                    else None
                ),
                artist=(
                    internal.ArtistSearchFilter(**query.artist_search_filter.model_dump())
                    if query.artist_search_filter is not None
                    else None
                ),
                composer=(
                    internal.ComposerSearchFilter(**query.composer_search_filter.model_dump())
                    if query.composer_search_filter is not None
                    else None
                ),
                and_logic=query.and_logic,
            )
            limit = 500
        case schemas.ArtistIdSearchRequest():
            criteria = internal.ArtistIdCriteria(
                tuple(query.artist_ids), _credit_options(query), id_match=query.id_match
            )
        case schemas.ComposerIdSearchRequest():
            criteria = internal.ComposerIdCriteria(
                tuple(query.composer_ids),
                _credit_options(query),
                query.arrangement,
                id_match=query.id_match,
            )
        case schemas.AnnIdSearchRequest():
            criteria = internal.ExternalIdCriteria("ann", (query.annId,))
        case schemas.AnnIdsSearchRequest():
            criteria = internal.ExternalIdCriteria("ann", tuple(query.ann_ids))
        case schemas.MalIdsSearchRequest():
            criteria = internal.ExternalIdCriteria("mal", tuple(query.mal_ids))
        case schemas.AnilistIdsSearchRequest():
            criteria = internal.ExternalIdCriteria("anilist", tuple(query.anilist_ids))
        case schemas.KitsuIdsSearchRequest():
            criteria = internal.ExternalIdCriteria("kitsu", tuple(query.kitsu_ids))
        case schemas.AnidbIdsSearchRequest():
            criteria = internal.ExternalIdCriteria("anidb", tuple(query.anidb_ids))
        case schemas.AnnSongIdsSearchRequest():
            criteria = internal.ExternalIdCriteria("ann-song", tuple(query.ann_song_ids))
        case schemas.AmqSongIdsSearchRequest():
            criteria = internal.ExternalIdCriteria("amq-song", tuple(query.amq_song_ids))
        case schemas.SeasonSearchRequest():
            criteria = internal.SeasonCriteria(_normalize_season(query.season))
        case schemas.GetNSongsRequest():
            criteria = internal.RandomCriteria(query.n)
        case _:
            raise TypeError(f"Unsupported search request: {type(query).__name__}")

    return internal.SearchQuery(
        criteria=criteria,
        filters=resolve_song_filters(query, catalog),
        ignore_duplicate=query.ignore_duplicate,
        limit=limit,
    )


def _credit_options(query: schemas.CreditSearchOptions) -> internal.CreditSearchOptions:
    return internal.CreditSearchOptions(
        group_granularity=query.group_granularity,
        max_other_artist=query.max_other_artist,
    )


def _normalize_season(value: str) -> str:
    """Preserve the season endpoint's whitespace normalization and 400 error details."""
    parts = " ".join(value.split()).split(" ")
    if len(parts) != 2:
        raise HTTPException(
            status_code=400, detail="Invalid season format. Please use 'Season Year'."
        )
    season, year = parts
    season = season.capitalize()
    if season not in ("Winter", "Spring", "Summer", "Fall"):
        raise HTTPException(
            status_code=400,
            detail="Invalid season. Please use 'Winter', 'Spring', 'Summer', or 'Fall'.",
        )
    if not year.isdigit() or len(year) != 4:
        raise HTTPException(status_code=400, detail="Invalid year. Please use a 4-digit year.")
    return f"{season} {year}"
