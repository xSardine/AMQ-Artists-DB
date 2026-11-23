import type { AnimeType, BroadcastType, SongCategory, SongType } from './search-command';

interface FilterOption<Value extends string> {
  key: string;
  label: string;
  idSuffix: string;
  values: readonly Value[];
}

export const SONG_TYPE_OPTIONS = [
  { key: 'openings', label: 'OP', idSuffix: 'op', values: ['opening'] },
  { key: 'endings', label: 'ED', idSuffix: 'ed', values: ['ending'] },
  { key: 'inserts', label: 'INS', idSuffix: 'ins', values: ['insert'] },
] as const satisfies readonly FilterOption<SongType>[];

const BROADCAST_OPTIONS = [
  { key: 'normalBroadcasts', label: 'Normal', idSuffix: 'normal-broadcasts', values: ['normal'] },
  { key: 'dubs', label: 'Dubs', idSuffix: 'dubs', values: ['dub'] },
  { key: 'rebroadcasts', label: 'Rebroadcasts', idSuffix: 'rebroadcasts', values: ['rebroadcast'] },
] as const satisfies readonly FilterOption<BroadcastType>[];

const PERFORMANCE_OPTIONS = [
  // Standard also includes songs without a category; there is no separate Other checkbox.
  { key: 'standards', label: 'Standard', idSuffix: 'standard', values: ['standard', 'other'] },
  { key: 'characters', label: 'Character', idSuffix: 'character', values: ['character'] },
  { key: 'chantings', label: 'Chanting', idSuffix: 'chanting', values: ['chanting'] },
  { key: 'instrumentals', label: 'Instrumental', idSuffix: 'instrumental', values: ['instrumental'] },
] as const satisfies readonly FilterOption<SongCategory>[];

const ANIME_TYPE_OPTIONS = [
  { key: 'tv', label: 'TV', idSuffix: 'tv', values: ['tv'] },
  { key: 'movie', label: 'Movie', idSuffix: 'movie', values: ['movie'] },
  { key: 'ova', label: 'OVA', idSuffix: 'ova', values: ['ova'] },
  { key: 'ona', label: 'ONA', idSuffix: 'ona', values: ['ona'] },
  { key: 'special', label: 'Special', idSuffix: 'special', values: ['special'] },
  { key: 'other', label: 'Other', idSuffix: 'other', values: ['other'] },
] as const satisfies readonly FilterOption<AnimeType>[];

export const ADVANCED_FILTER_GROUPS = [
  { id: 'song-type', label: 'Song Type', options: SONG_TYPE_OPTIONS },
  { id: 'broadcast', label: 'Broadcast', options: BROADCAST_OPTIONS },
  { id: 'performance', label: 'Performance', options: PERFORMANCE_OPTIONS },
  { id: 'anime-type', label: 'Anime Type', options: ANIME_TYPE_OPTIONS },
] as const;

const ALL_FILTER_OPTIONS = [
  ...SONG_TYPE_OPTIONS,
  ...BROADCAST_OPTIONS,
  ...PERFORMANCE_OPTIONS,
  ...ANIME_TYPE_OPTIONS,
];

type FilterKey = typeof ALL_FILTER_OPTIONS[number]['key'];

export type SearchFilterSelection = Record<FilterKey, boolean> & {
  includeNoLinks: boolean;
};

export function createDefaultSearchFilters(): SearchFilterSelection {
  const selected = Object.fromEntries(
    ALL_FILTER_OPTIONS.map(option => [option.key, true]),
  ) as Record<FilterKey, boolean>;
  return { ...selected, includeNoLinks: true };
}

function selectedValues<Value extends string>(
  selected: SearchFilterSelection,
  options: readonly { key: FilterKey; values: readonly Value[] }[],
): Value[] {
  return options.flatMap(option => selected[option.key] ? [...option.values] : []);
}

export function selectedSearchFilters(selected: SearchFilterSelection) {
  return {
    song_types: selectedValues(selected, SONG_TYPE_OPTIONS),
    broadcasts: selectedValues(selected, BROADCAST_OPTIONS),
    song_categories: selectedValues(selected, PERFORMANCE_OPTIONS),
    anime_types: selectedValues(selected, ANIME_TYPE_OPTIONS),
  };
}
