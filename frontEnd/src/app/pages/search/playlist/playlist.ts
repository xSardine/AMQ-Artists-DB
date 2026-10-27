export type Playlist = {
  id: string;
  name: string;
  createdOn: string;
  annSongIds: number[];
};

export type PlaylistAddResult =
  | 'added'
  | 'duplicate'
  | 'full'
  | 'invalid-song'
  | 'not-found';

export type PlaylistToggleResult = PlaylistAddResult | 'removed';

export type PlaylistAppendResult = {
  addedCount: number;
  duplicateCount: number;
  skippedForLimitCount: number;
};

type PlaylistComparator = (left: Playlist, right: Playlist) => number;

export const PLAYLIST_SORT_OPTIONS = [
  {
    value: 'created-desc',
    label: 'Newest first',
    compare: (left, right) =>
      compareCreated(left, right, 'desc') || compareNames(left, right),
  },
  {
    value: 'created-asc',
    label: 'Oldest first',
    compare: (left, right) =>
      compareCreated(left, right, 'asc') || compareNames(left, right),
  },
  {
    value: 'name-asc',
    label: 'Name A–Z',
    compare: (left, right) =>
      compareNames(left, right) || compareCreated(left, right, 'asc'),
  },
  {
    value: 'name-desc',
    label: 'Name Z–A',
    compare: (left, right) =>
      compareNames(right, left) || compareCreated(left, right, 'desc'),
  },
  {
    value: 'size-desc',
    label: 'Most songs',
    compare: (left, right) =>
      right.annSongIds.length - left.annSongIds.length || compareNames(left, right),
  },
  {
    value: 'size-asc',
    label: 'Fewest songs',
    compare: (left, right) =>
      left.annSongIds.length - right.annSongIds.length || compareNames(left, right),
  },
] as const satisfies readonly {
  value: string;
  label: string;
  compare: PlaylistComparator;
}[];

export type PlaylistSort = typeof PLAYLIST_SORT_OPTIONS[number]['value'];

export const DEFAULT_PLAYLIST_SORT: PlaylistSort = 'created-desc';

function isPlaylistSort(value: unknown): value is PlaylistSort {
  return typeof value === 'string'
    && PLAYLIST_SORT_OPTIONS.some((option) => option.value === value);
}

export function parsePlaylistSort(value: unknown): PlaylistSort {
  return isPlaylistSort(value) ? value : DEFAULT_PLAYLIST_SORT;
}

export function sortPlaylists(playlists: Playlist[], sort: PlaylistSort): Playlist[] {
  const option = PLAYLIST_SORT_OPTIONS.find((candidate) => candidate.value === sort);
  return option ? [...playlists].sort(option.compare) : [...playlists];
}

function compareNames(left: Playlist, right: Playlist): number {
  return left.name.localeCompare(right.name, undefined, { sensitivity: 'base' });
}

function compareCreated(
  left: Playlist,
  right: Playlist,
  direction: 'asc' | 'desc',
): number {
  const leftTime = Date.parse(left.createdOn);
  const rightTime = Date.parse(right.createdOn);
  const leftValid = Number.isFinite(leftTime);
  const rightValid = Number.isFinite(rightTime);

  if (!leftValid && !rightValid) return compareNames(left, right);
  if (!leftValid) return 1;
  if (!rightValid) return -1;

  const difference = leftTime - rightTime;
  return direction === 'asc' ? difference : -difference;
}
