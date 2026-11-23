"""Artist relationship traversal, with per-snapshot memoization and cycle detection."""

from catalog.models import (
    ArtistDatabase,
    CatalogLoadError,
    Credits,
)


class CreditGraph:
    def __init__(self, artists: ArtistDatabase):
        self.artists = artists
        self._flattened: dict[tuple[Credits, bool], frozenset[int]] = {}
        self._parents: dict[int, tuple[tuple[int, int], ...]] = {}

    def flatten(self, credits: Credits, bottom: bool = True) -> frozenset[int]:
        return self._flatten(credits, bottom, set())

    def _flatten(
        self, credits: Credits, bottom: bool, visiting: set[tuple[int, int]]
    ) -> frozenset[int]:
        key = (credits, bottom)
        if key in self._flattened:
            return self._flattened[key]
        members = set()
        for artist_id, lineup in credits:
            if lineup < -1:
                raise CatalogLoadError(f"Invalid artist lineup: {(artist_id, lineup)}")
            if lineup == -1:
                members.add(artist_id)
                continue
            pair = (artist_id, lineup)
            if pair in visiting:
                raise CatalogLoadError(f"Cyclic artist lineup: {pair}")
            if not bottom:
                members.add(artist_id)
            artist = self.artists.get(artist_id)
            if not artist or lineup >= len(artist.line_ups):
                continue
            members.update(
                self._flatten(artist.line_ups[lineup].members, bottom, visiting | {pair})
            )
        result = frozenset(members)
        self._flattened[key] = result
        return result

    def parent_groups(self, artist_id: int) -> tuple[tuple[int, int], ...]:
        return self._parent_groups(artist_id, set())

    def _parent_groups(self, artist_id: int, visiting: set[int]) -> tuple[tuple[int, int], ...]:
        if artist_id in visiting:
            raise CatalogLoadError(f"Cyclic artist group: {artist_id}")
        if artist_id in self._parents:
            return self._parents[artist_id]
        entry = self.artists.get(artist_id)
        groups = []
        if entry:
            for group_id, lineup in entry.groups:
                if lineup < -1:
                    raise CatalogLoadError(
                        f"Invalid group lineup for artist {artist_id}: {(group_id, lineup)}"
                    )
                groups.append((group_id, lineup))
                groups.extend(self._parent_groups(group_id, visiting | {artist_id}))
        result = tuple(groups)
        self._parents[artist_id] = result
        return result

    def validate(self) -> None:
        """Reject cycles before serving requests; prime stable relationship caches."""
        for artist_id, artist in self.artists.items():
            self.parent_groups(artist_id)
            for lineup in artist.line_ups:
                self.flatten(lineup.members)
