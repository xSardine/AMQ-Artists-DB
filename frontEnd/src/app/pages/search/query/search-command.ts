export type SongId = string | number;
export type IdMatch = 'any' | 'all';

export interface TextSearchFilter {
  search: string;
  partial_match?: boolean;
  match_case?: boolean;
}

export interface CreditSearchOptions {
  group_granularity?: number;
  max_other_artist?: number;
}

export interface ArtistSearchFilter extends TextSearchFilter, CreditSearchOptions {}

export interface ComposerSearchFilter extends ArtistSearchFilter {
  arrangement?: boolean;
}

export const DEFAULT_CREDIT_OPTIONS = {
  group_granularity: 0,
  max_other_artist: 99,
} as const satisfies CreditSearchOptions;

export type SongLinkType = 'audio' | 'mq' | 'hq';

export interface MediaLinksFilter {
  require_any?: SongLinkType[];
  require_all?: SongLinkType[];
  exclude?: SongLinkType[];
}

export type SongType = 'opening' | 'ending' | 'insert';
export type BroadcastType = 'normal' | 'dub' | 'rebroadcast';
export type SongCategory = 'standard' | 'character' | 'chanting' | 'instrumental' | 'other';
export type AnimeType = 'tv' | 'movie' | 'ova' | 'ona' | 'special' | 'other';

export interface SeasonFilter {
  start?: string;
  end?: string;
}

export interface DifficultyFilter {
  start?: number;
  end?: number;
}

export interface SongLengthFilter {
  start?: number;
  end?: number;
}

export interface AnimeLabelsFilter {
  require_all?: string[];
}

export interface SongSearchFilters {
  song_types?: SongType[];
  broadcasts?: BroadcastType[];
  song_categories?: SongCategory[];
  anime_types?: AnimeType[];
  season?: SeasonFilter;
  difficulty?: DifficultyFilter;
  song_length?: SongLengthFilter;
  genres?: AnimeLabelsFilter;
  tags?: AnimeLabelsFilter;
  media_links?: MediaLinksFilter;
}

export interface SearchOptions {
  ignore_duplicate?: boolean;
  filters?: SongSearchFilters;
}

export interface TextSearchBody extends SearchOptions {
  anime_search_filter?: TextSearchFilter;
  song_name_search_filter?: TextSearchFilter;
  artist_search_filter?: ArtistSearchFilter;
  composer_search_filter?: ComposerSearchFilter;
  and_logic?: boolean;
}

/** Each operation accepts only the options its endpoint implements. */
export interface SearchBodies {
  random: SearchOptions & { n: number };
  general: TextSearchBody;
  season: SearchOptions & { season: string };
  'ann-ids': SearchOptions & { ann_ids: SongId[] };
  'mal-ids': SearchOptions & { mal_ids: SongId[] };
  'anilist-ids': SearchOptions & { anilist_ids: SongId[] };
  'kitsu-ids': SearchOptions & { kitsu_ids: SongId[] };
  'anidb-ids': SearchOptions & { anidb_ids: SongId[] };
  'ann-song-ids': SearchOptions & { ann_song_ids: SongId[] };
  'amq-song-ids': SearchOptions & { amq_song_ids: SongId[] };
  'artist-ids': SearchOptions & CreditSearchOptions & {
    artist_ids: number[];
    id_match?: IdMatch;
  };
  'composer-ids': SearchOptions & CreditSearchOptions & {
    composer_ids: number[];
    arrangement?: boolean;
    id_match?: IdMatch;
  };
}

/** Identifies the search operation independently from its API payload. */
export type SearchCommand =
  | { kind: 'initial-random' }
  | { [K in keyof SearchBodies]: { kind: K; body: SearchBodies[K] } }[keyof SearchBodies];

