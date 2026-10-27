import { parseNonNegativeInteger } from '../../../shared/utils/number';
import { parseAnimeSeason } from '../songs/song-metadata';
import {
  createDefaultSearchFilters,
  selectedSearchFilters,
  type SearchFilterSelection,
} from './search-filter-options';
import {
  type TextSearchFilter,
  type CreditSearchOptions,
  type IdMatch,
  DEFAULT_CREDIT_OPTIONS,
  type SongSearchFilters,
  type SearchOptions,
  type SearchCommand,
} from './search-command';

type IdSearchKind = Extract<SearchCommand['kind'], `${string}-ids`>;

type LookupCreditOptions = CreditSearchOptions & { arrangement?: boolean; id_match?: IdMatch };

interface IdLookupDefinition {
  keyword: string;
  value: IdSearchKind;
  label: string;
  placeholder: string;
  inputMode: null;
  buildCommand: (ids: number[], options: SearchOptions, credit: LookupCreditOptions) => SearchCommand;
}

function defineIdLookup<const K extends IdSearchKind>(
  keyword: string,
  value: K,
  label: string,
  buildCommand: (
    ids: number[],
    options: SearchOptions,
    credit: LookupCreditOptions,
  ) => Extract<SearchCommand, { kind: K }>,
) {
  return { keyword, value, label, placeholder: '1, 2, 3', inputMode: null, buildCommand } as const;
}

const ID_LOOKUPS = [
  defineIdLookup('annid', 'ann-ids', 'ANN ID', (ids, options) => ({
    kind: 'ann-ids', body: { ...options, ann_ids: ids },
  })),
  defineIdLookup('malid', 'mal-ids', 'MAL ID', (ids, options) => ({
    kind: 'mal-ids', body: { ...options, mal_ids: ids },
  })),
  defineIdLookup('anilistid', 'anilist-ids', 'AniList ID', (ids, options) => ({
    kind: 'anilist-ids', body: { ...options, anilist_ids: ids },
  })),
  defineIdLookup('kitsuid', 'kitsu-ids', 'Kitsu ID', (ids, options) => ({
    kind: 'kitsu-ids', body: { ...options, kitsu_ids: ids },
  })),
  defineIdLookup('anidbid', 'anidb-ids', 'AniDB ID', (ids, options) => ({
    kind: 'anidb-ids', body: { ...options, anidb_ids: ids },
  })),
  defineIdLookup('annsongid', 'ann-song-ids', 'ANN Song ID', (ids, options) => ({
    kind: 'ann-song-ids', body: { ...options, ann_song_ids: ids },
  })),
  defineIdLookup('amqsongid', 'amq-song-ids', 'AMQ Song ID', (ids, options) => ({
    kind: 'amq-song-ids', body: { ...options, amq_song_ids: ids },
  })),
  defineIdLookup('artistid', 'artist-ids', 'Artist ID', (ids, options, credit) => ({
    kind: 'artist-ids',
    body: {
      ...options,
      artist_ids: ids,
      group_granularity: credit.group_granularity,
      max_other_artist: credit.max_other_artist,
      id_match: credit.id_match,
    },
  })),
  defineIdLookup('composerid', 'composer-ids', 'Composer ID', (ids, options, credit) => ({
    kind: 'composer-ids', body: { ...options, ...credit, composer_ids: ids },
  })),
] as const satisfies readonly IdLookupDefinition[];

const SEASON_LOOKUP_OPTION = {
  value: 'season', label: 'Season', placeholder: 'Winter 2020', inputMode: null,
} as const;

export const ADVANCED_LOOKUP_OPTIONS = [
  SEASON_LOOKUP_OPTION,
  ...ID_LOOKUPS,
  { value: 'random', label: 'Random # Songs', placeholder: '#', inputMode: 'numeric' },
] as const;

export type AdvancedLookupType = typeof ADVANCED_LOOKUP_OPTIONS[number]['value'];

export function getAdvancedLookupOption(type: AdvancedLookupType) {
  return ADVANCED_LOOKUP_OPTIONS.find((option) => option.value === type) ?? SEASON_LOOKUP_OPTION;
}

const MAX_ID_SEARCH_COUNT = 500;
const MAX_RANDOM_SONG_COUNT = 500;

export const SEARCH_MATCH_MODE_OPTIONS = [
  { value: 'partial', label: 'Partial Match' },
  { value: 'exact', label: 'Exact Match' },
  { value: 'partial-case', label: 'Partial + Case' },
  { value: 'exact-case', label: 'Exact + Case' },
] as const;

type SearchMatchMode = typeof SEARCH_MATCH_MODE_OPTIONS[number]['value'];
type AdvancedSearchFieldMode = 'text' | 'lookup';
type SearchCombination = 'or' | 'and';

export type SearchFormState = {
  main: string;
  mainPartialMatch: boolean;
  anime: string;
  songName: string;
  artist: string;
  composer: string;
  advancedSearchFieldMode: AdvancedSearchFieldMode;
  advancedLookupType: AdvancedLookupType;
  advancedLookupValue: string;
  idMatch: IdMatch;
  seasonRange: string;
  difficultyRange: string;
  songLengthRange: string;
  genres: string;
  tags: string;
  maximumOtherPeople: number | null;
  minimumGroupMembers: number | null;
  combination: SearchCombination;
  animeMatchMode: SearchMatchMode;
  songNameMatchMode: SearchMatchMode;
  artistMatchMode: SearchMatchMode;
  composerMatchMode: SearchMatchMode;
  composerArrangement: boolean;
  ignoreDuplicate: boolean;
  filters: SearchFilterSelection;
};

type SearchCommandBuildResult =
  | { command: SearchCommand }
  | { error: string };

export function createDefaultSearchFormState(): SearchFormState {
  return {
    main: '',
    mainPartialMatch: true,
    anime: '',
    songName: '',
    artist: '',
    composer: '',
    advancedSearchFieldMode: 'text',
    advancedLookupType: 'season',
    advancedLookupValue: '',
    idMatch: 'any',
    seasonRange: '',
    difficultyRange: '',
    songLengthRange: '',
    genres: '',
    tags: '',
    maximumOtherPeople: DEFAULT_CREDIT_OPTIONS.max_other_artist,
    minimumGroupMembers: DEFAULT_CREDIT_OPTIONS.group_granularity,
    combination: 'or',
    animeMatchMode: 'partial',
    songNameMatchMode: 'partial',
    artistMatchMode: 'partial',
    composerMatchMode: 'partial',
    composerArrangement: true,
    ignoreDuplicate: false,
    filters: createDefaultSearchFilters(),
  };
}

function parseSeasonQuery(text: string): string | null {
  return parseAnimeSeason(text)?.label ?? null;
}

type SearchRange<T> = {
  start?: T;
  end?: T;
};

function parseRangeQuery<T>(
  text: string,
  parseValue: (value: string) => T | null,
): SearchRange<T> | null | undefined {
  const input = text.trim();
  if (!input) return undefined;

  const values = input.split(/\s*[-\u2013\u2014]\s*/);
  if (values.length > 2) return null;

  if (values.length === 1) {
    const value = parseValue(values[0]);
    return value === null ? null : { start: value, end: value };
  }

  const [startInput, endInput] = values;
  if (!startInput && !endInput) return undefined;

  const start = startInput ? parseValue(startInput) : undefined;
  const end = endInput ? parseValue(endInput) : undefined;
  if ((startInput && start === null) || (endInput && end === null)) return null;

  return {
    start: start ?? undefined,
    end: end ?? undefined,
  };
}

function parseNonNegativeNumberQuery(text: string): number | null {
  const input = text.trim();
  if (!/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(input)) return null;

  const value = Number(input);
  return Number.isFinite(value) ? value : null;
}

function parseDifficultyQuery(text: string): number | null {
  const difficulty = parseNonNegativeNumberQuery(text.trim().replace(/%$/, ''));
  return difficulty !== null && difficulty <= 100 ? difficulty : null;
}

function parseAnimeLabelsQuery(text: string): string[] | null | undefined {
  if (!text.trim()) return undefined;
  const labels = text.split(',').map(label => label.trim());
  if (labels.length > 100 || labels.some(label => !label || label.length > 500)) return null;

  const uniqueLabels = new Map(labels.map(label => [label.toLowerCase(), label]));
  return [...uniqueLabels.values()];
}

/** A recognized keyword stays an ID query even when its values are invalid. */
function parseIdListQuery(text: string): { config: IdLookupDefinition; ids: number[] | null } | null {
  const match = text.trim().match(/^(\S+)(?:\s+([\s\S]*))?$/);
  if (!match) return null;

  const config = ID_LOOKUPS.find((candidate) => candidate.keyword === match[1].toLowerCase());
  return config ? { config, ids: parseIdListValues(match[2] ?? '') } : null;
}

function parseIdListValues(text: string): number[] | null {
  const ids: number[] = [];
  const idOrRangePattern = /\d+(?:\s*-\s*\d+)?/g;
  let cursor = 0;

  for (const part of text.matchAll(idOrRangePattern)) {
    if (!/^[,\s]*$/.test(text.slice(cursor, part.index))) return null;

    const values = part[0].split(/\s*-\s*/).map(Number);
    if (values.some((value) => !Number.isSafeInteger(value))) return null;

    const [start, end = values[0]] = values;
    const rangeSize = Math.abs(end - start) + 1;
    if (ids.length + rangeSize > MAX_ID_SEARCH_COUNT) return null;

    const step = start <= end ? 1 : -1;
    for (let id = start; step === 1 ? id <= end : id >= end; id += step) {
      ids.push(id);
    }
    cursor = part.index + part[0].length;
  }

  return ids.length && /^[,\s]*$/.test(text.slice(cursor)) ? ids : null;
}

export function buildSearchCommand(
  state: SearchFormState,
  advanced: boolean,
  rankedActive: boolean,
): SearchCommandBuildResult {
  const result = buildSongFilters(state, advanced);
  if ('error' in result) return result;

  const options: SearchOptions = {
    filters: result.filters,
    ignore_duplicate: state.ignoreDuplicate,
  };
  return advanced
    ? buildAdvancedSearchCommand(state, options)
    : buildSimpleSearchCommand(state, options, rankedActive);
}

function buildSongFilters(
  state: SearchFormState,
  advanced: boolean,
): { filters: SongSearchFilters } | { error: string } {
  const {
    song_types: songTypes,
    broadcasts,
    song_categories: songCategories,
    anime_types: animeTypes,
  } = selectedSearchFilters(state.filters);
  if (!songTypes.length) {
    return invalidSearch('At least one song type filter (OP, ED, INS) must be enabled.');
  }
  if (!advanced) return { filters: { song_types: songTypes } };

  if (!broadcasts.length) {
    return invalidSearch('At least one broadcast filter (Normal, Dubs, Rebroadcasts) must be enabled.');
  }
  if (!songCategories.length) {
    return invalidSearch('At least one performance filter (Standard, Character, Chanting, Instrumental) must be enabled.');
  }
  if (!animeTypes.length) {
    return invalidSearch('At least one anime type filter (TV, Movie, OVA, ONA, Special, Other) must be enabled.');
  }

  const season = parseRangeQuery(state.seasonRange, parseSeasonQuery);
  if (season === null) {
    return invalidSearch('Enter a season or range like "Winter 2020", "Winter 2020 - Fall 2024", or "- Fall 2024".');
  }
  const difficulty = parseRangeQuery(state.difficultyRange, parseDifficultyQuery);
  if (difficulty === null) {
    return invalidSearch('Enter a difficulty from 0 to 100, or a range like "20 - 80", "20 -", or "- 80".');
  }
  const songLength = parseRangeQuery(state.songLengthRange, parseNonNegativeNumberQuery);
  if (songLength === null) {
    return invalidSearch('Enter a song length in seconds, or a range like "90 - 180", "90 -", or "- 180".');
  }
  const genres = parseAnimeLabelsQuery(state.genres);
  if (genres === null) {
    return invalidSearch('Enter up to 100 comma-separated genre names without empty entries.');
  }
  const tags = parseAnimeLabelsQuery(state.tags);
  if (tags === null) {
    return invalidSearch('Enter up to 100 comma-separated tag names without empty entries.');
  }

  return {
    filters: {
      song_types: songTypes,
      broadcasts,
      song_categories: songCategories,
      anime_types: animeTypes,
      season,
      difficulty,
      song_length: songLength,
      genres: genres ? { require_all: genres } : undefined,
      tags: tags ? { require_all: tags } : undefined,
      media_links: state.filters.includeNoLinks ? undefined : { require_any: ['audio', 'mq', 'hq'] },
    },
  };
}

function buildSimpleSearchCommand(
  state: SearchFormState,
  options: SearchOptions,
  rankedActive: boolean,
): SearchCommandBuildResult {
  const main = state.main.trim();
  if (!main) return invalidSearch('Enter at least one search term.');

  const season = parseSeasonQuery(main);
  if (season) return validSearch({ kind: 'season', body: { ...options, season } });

  const idQuery = parseIdListQuery(main);
  if (idQuery) {
    return idQuery.ids
      ? validSearch(idQuery.config.buildCommand(idQuery.ids, options, DEFAULT_CREDIT_OPTIONS))
      : invalidSearch(idListError(idQuery.config.label));
  }

  const textFilter: TextSearchFilter = { search: main, partial_match: state.mainPartialMatch };
  return validSearch({
    kind: 'general',
    body: {
      ...options,
      anime_search_filter: textFilter,
      ...(!rankedActive && {
        song_name_search_filter: textFilter,
        artist_search_filter: textFilter,
        composer_search_filter: textFilter,
      }),
      // Simple search always matches any field; the API default is AND.
      and_logic: false,
    },
  });
}

function buildAdvancedSearchCommand(
  state: SearchFormState,
  options: SearchOptions,
): SearchCommandBuildResult {
  if (state.advancedSearchFieldMode === 'lookup') {
    return buildAdvancedLookupCommand(state, options);
  }

  const anime = buildTextSearchFilter(state.anime, state.animeMatchMode);
  const songName = buildTextSearchFilter(state.songName, state.songNameMatchMode);
  const artist = buildTextSearchFilter(state.artist, state.artistMatchMode);
  const composer = buildTextSearchFilter(state.composer, state.composerMatchMode);
  if (!anime && !songName && !artist && !composer) {
    return invalidSearch('Enter at least one search term.');
  }

  const result = artist || composer ? buildCreditOptions(state) : { credit: DEFAULT_CREDIT_OPTIONS };
  if ('error' in result) return result;

  return validSearch({
    kind: 'general',
    body: {
      ...options,
      anime_search_filter: anime,
      song_name_search_filter: songName,
      artist_search_filter: artist ? { ...artist, ...result.credit } : undefined,
      composer_search_filter: composer
        ? { ...composer, ...result.credit, arrangement: state.composerArrangement }
        : undefined,
      and_logic: state.combination === 'and',
    },
  });
}

function buildAdvancedLookupCommand(
  state: SearchFormState,
  options: SearchOptions,
): SearchCommandBuildResult {
  const type = state.advancedLookupType;
  const input = state.advancedLookupValue.trim();

  if (type === 'season') {
    const season = parseSeasonQuery(input);
    return season
      ? validSearch({ kind: 'season', body: { ...options, season } })
      : invalidSearch('Enter a season like "Winter 2020".');
  }
  if (type === 'random') {
    const count = parseWholeNumber(input);
    return count !== null && count >= 1 && count <= MAX_RANDOM_SONG_COUNT
      ? validSearch({ kind: 'random', body: { ...options, n: count } })
      : invalidSearch(`Enter a whole number from 1 to ${MAX_RANDOM_SONG_COUNT}.`);
  }

  const config = ID_LOOKUPS.find((candidate) => candidate.value === type);
  if (!config) return invalidSearch('Choose a valid lookup field.');
  const ids = parseIdListValues(input);
  if (!ids) return invalidSearch(idListError(config.label));

  const result = type === 'artist-ids' || type === 'composer-ids'
    ? buildCreditOptions(state)
    : { credit: DEFAULT_CREDIT_OPTIONS };
  if ('error' in result) return result;

  return validSearch(config.buildCommand(ids, options, {
    ...result.credit,
    arrangement: state.composerArrangement,
    id_match: state.idMatch,
  }));
}

function buildCreditOptions(
  state: SearchFormState,
): { credit: Required<CreditSearchOptions> } | { error: string } {
  const maxOtherArtist = parseNonNegativeInteger(state.maximumOtherPeople);
  if (maxOtherArtist === null) {
    return invalidSearch('Max Other People must be a whole number of 0 or greater.');
  }
  const groupGranularity = parseNonNegativeInteger(state.minimumGroupMembers);
  if (groupGranularity === null) {
    return invalidSearch('Min Group Members must be a whole number of 0 or greater.');
  }
  return { credit: { group_granularity: groupGranularity, max_other_artist: maxOtherArtist } };
}

function buildTextSearchFilter(text: string, matchMode: SearchMatchMode): TextSearchFilter | undefined {
  const search = text.trim();
  return search ? {
    search,
    partial_match: matchMode === 'partial' || matchMode === 'partial-case',
    match_case: matchMode === 'partial-case' || matchMode === 'exact-case',
  } : undefined;
}

function validSearch(command: SearchCommand): { command: SearchCommand } {
  return { command };
}

function invalidSearch(error: string): { error: string } {
  return { error };
}

function idListError(label: string): string {
  return `Enter up to ${MAX_ID_SEARCH_COUNT} ${label}s using commas or ranges, like "1, 5-10, 25".`;
}

function parseWholeNumber(value: string): number | null {
  const input = value.trim();
  return /^\d+$/.test(input) ? parseNonNegativeInteger(input) : null;
}
