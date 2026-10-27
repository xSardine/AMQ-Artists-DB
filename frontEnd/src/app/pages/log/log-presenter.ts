import { LogEvent, LogTimeSettings, RequestGroup } from './log-types';

type LogBody = Record<string, unknown>;

export interface LogQuery {
  label: string;
  value: string;
  count?: number;
  options: string[];
}

export interface LogDescription {
  request: string;
  queries: LogQuery[];
  filters: LogFilterRow[];
}

export interface LogFilterRow {
  label: string;
  entries: LogFilterEntry[];
}

export interface LogFilterEntry {
  values: string[];
  operator?: 'Any' | 'All' | 'Exclude';
}

export interface LogValidationIssue {
  location: string;
  message: string;
}

const ENDPOINT_LABELS: Record<string, string> = {
  '/api/search_request': 'Search',
  '/api/ann_ids_request': 'ANN IDs',
  '/api/mal_ids_request': 'MAL IDs',
  '/api/anilist_ids_request': 'AniList IDs',
  '/api/kitsu_ids_request': 'Kitsu IDs',
  '/api/anidb_ids_request': 'AniDB IDs',
  '/api/ann_song_ids_request': 'ANN song IDs',
  '/api/amq_song_ids_request': 'AMQ song IDs',
  '/api/season_request': 'Season',
  '/api/get_n_random_songs': 'Random songs',
  '/api/artist_ids_request': 'Artist IDs',
  '/api/composer_ids_request': 'Composer IDs',
  '/api/annId_request': 'ANN ID',
};

const ID_FIELDS = [
  ['artist_ids', 'Artist IDs'],
  ['composer_ids', 'Composer IDs'],
  ['ann_ids', 'ANN IDs'],
  ['mal_ids', 'MAL IDs'],
  ['anilist_ids', 'AniList IDs'],
  ['kitsu_ids', 'Kitsu IDs'],
  ['anidb_ids', 'AniDB IDs'],
  ['ann_song_ids', 'ANN song IDs'],
  ['amq_song_ids', 'AMQ song IDs'],
] as const;

const SEARCH_FIELDS = [
  ['anime_search_filter', 'Anime'],
  ['song_name_search_filter', 'Song'],
  ['artist_search_filter', 'Artist'],
  ['composer_search_filter', 'Composer'],
] as const;

const SELECTION_FILTERS = [
  {
    key: 'song_types', label: 'Song types',
    defaults: ['opening', 'ending', 'insert'],
    names: { opening: 'OP', ending: 'ED', insert: 'IN' },
  },
  { key: 'broadcasts', label: 'Broadcasts', defaults: ['normal', 'dub', 'rebroadcast'] },
  {
    key: 'song_categories', label: 'Performance',
    defaults: ['standard', 'character', 'chanting', 'instrumental', 'other'],
  },
  {
    key: 'anime_types', label: 'Anime types',
    defaults: ['tv', 'movie', 'ova', 'ona', 'special', 'other'],
  },
] as const;

const REQUIREMENT_GROUPS = [
  { key: 'media_links', label: 'Links' },
  { key: 'genres', label: 'Genres' },
  { key: 'tags', label: 'Tags' },
] as const;

function objectValue(value: unknown): LogBody {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as LogBody : {};
}

function valueText(value: unknown): string {
  if (value == null) return '—';
  if (typeof value === 'string') return value;
  return JSON.stringify(value) ?? '—';
}

export function endpointLabel(path: string): string {
  return ENDPOINT_LABELS[path] ?? path.replace(/^\/api\//, '').replaceAll('_', ' ');
}

export function requestGroupForEndpoint(path: string): RequestGroup {
  if (path === '/api/search_request') return 'text';
  return path === '/api/annId_request' || ID_FIELDS.some(([key]) => path === `/api/${key}_request`)
    ? 'ids' : 'other';
}

function queryOptions(filter: LogBody): string[] {
  const options: string[] = [];
  if (filter.partial_match === false) options.push('Exact match');
  if (filter.match_case === true) options.push('Match case');
  if (filter.group_granularity !== undefined && filter.group_granularity !== 0) {
    options.push(`Min group members: ${valueText(filter.group_granularity)}`);
  }
  if (filter.max_other_artist !== undefined && filter.max_other_artist !== 99) {
    options.push(`Max other artists: ${valueText(filter.max_other_artist)}`);
  }
  if (filter.arrangement === false) options.push('No arrangements');
  return options;
}

function describeQueries(event: LogEvent, body: LogBody): LogQuery[] {
  const queries: LogQuery[] = [];
  for (const [key, label] of ID_FIELDS) {
    const ids = body[key];
    if (Array.isArray(ids) && ids.length) {
      const options: string[] = [];
      if (key === 'artist_ids' || key === 'composer_ids') {
        if (ids.length > 1) {
          if (body.id_match === 'any') options.push('OR');
          if (body.id_match === 'all') options.push('AND');
        }
        options.push(...queryOptions(body));
      }
      queries.push({ label, value: ids.map(valueText).join(', '), count: ids.length, options });
    }
  }
  const scalarFields = [
    ['/api/annId_request', 'annId', 'ANN ID'],
    ['/api/season_request', 'season', 'Season'],
    ['/api/get_n_random_songs', 'n', 'Number of songs'],
  ] as const;
  for (const [endpoint, key, label] of scalarFields) {
    if (event.endpoint === endpoint && body[key] != null) {
      queries.push({ label, value: valueText(body[key]), options: [] });
    }
  }
  const searchQueries: LogQuery[] = [];
  for (const [key, label] of SEARCH_FIELDS) {
    const filter = objectValue(body[key]);
    if (typeof filter.search === 'string' && filter.search.trim()) {
      searchQueries.push({ label, value: filter.search, options: queryOptions(filter) });
    }
  }
  const first = searchQueries[0];
  const unified = searchQueries.length === SEARCH_FIELDS.length && searchQueries.every(query =>
    query.value === first.value && JSON.stringify(query.options) === JSON.stringify(first.options)
  );
  if (unified) queries.push({ ...first, label: 'All fields' });
  else queries.push(...searchQueries);
  return queries;
}

function rangeValues(filter: LogBody, unit = '', unknownKey?: string): string[] {
  const values: string[] = [];
  if (filter.start != null && filter.end != null) {
    values.push(`${valueText(filter.start)} – ${valueText(filter.end)}${unit}`);
  } else if (filter.start != null) {
    values.push(`From ${valueText(filter.start)}${unit}`);
  } else if (filter.end != null) {
    values.push(`Up to ${valueText(filter.end)}${unit}`);
  }
  if (unknownKey && filter[unknownKey] === true) {
    values.push(values.length ? 'Include unknown' : 'Unknown only');
  }
  return values;
}

function describeFilters(body: LogBody): LogFilterRow[] {
  const rows: LogFilterRow[] = [];
  const searchCount = SEARCH_FIELDS.filter(([key]) => {
    const search = objectValue(body[key]).search;
    return typeof search === 'string' && search.trim();
  }).length;
  if (searchCount > 1) {
    rows.push({ label: 'Match fields', entries: [{ values: [body.and_logic === false ? 'OR' : 'AND'] }] });
  }
  if (body.ignore_duplicate === true) {
    rows.push({ label: 'Duplicates', entries: [{ values: ['Ignored'] }] });
  }

  const filters = objectValue(body.filters);
  for (const filter of SELECTION_FILTERS) {
    const values = filters[filter.key];
    if (!Array.isArray(values)) continue;
    const selected = new Set<unknown>(values);
    if (selected.size === filter.defaults.length && filter.defaults.every(value => selected.has(value))) continue;
    const names: Record<string, string> = 'names' in filter ? filter.names : {};
    const selections = values.map(value => names[String(value).toLowerCase()] ?? valueText(value));
    rows.push({ label: filter.label, entries: [{ values: selections.length ? selections : ['None'] }] });
  }
  for (const [key, label, unit, unknownKey] of [
    ['season', 'Season', '', undefined],
    ['difficulty', 'Difficulty', '%', 'include_no_difficulty'],
    ['song_length', 'Length', ' sec', 'include_no_length'],
  ] as const) {
    const values = rangeValues(objectValue(filters[key]), unit, unknownKey);
    if (values.length) rows.push({ label, entries: [{ values }] });
  }

  for (const group of REQUIREMENT_GROUPS) {
    const filter = objectValue(filters[group.key]);
    const entries: LogFilterEntry[] = [];
    for (const [key, operator] of [
      ['require_any', 'Any'], ['require_all', 'All'], ['exclude', 'Exclude'],
    ] as const) {
      const values = filter[key];
      if (Array.isArray(values) && values.length) {
        entries.push({ operator, values: values.map(valueText) });
      }
    }
    if (entries.length) rows.push({ label: group.label, entries });
  }
  return rows;
}

export function formatLogFilters(rows: LogFilterRow[]): string[] {
  return rows.flatMap(row => row.entries.map(entry => {
    const label = [row.label, entry.operator].filter(Boolean).join(' ');
    return `${label}: ${entry.values.join(', ')}`;
  }));
}

export function describeLogEvent(event: LogEvent): LogDescription {
  const body = objectValue(event.body);
  const queries = describeQueries(event, body);
  return { request: endpointLabel(event.endpoint), queries, filters: describeFilters(body) };
}

export function describeLogErrors(errors: unknown): LogValidationIssue[] {
  if (errors == null) return [];
  if (!Array.isArray(errors)) return [{ location: 'Request', message: valueText(errors) }];
  return errors.map(value => {
    const error = objectValue(value);
    const path = Array.isArray(error.loc) ? [...error.loc] : [];
    if (path[0] === 'body') path.shift();
    return {
      location: path.map(valueText).join('.') || 'Request',
      message: typeof error.msg === 'string' ? error.msg : valueText(value),
    };
  });
}

export function eventSearchBlob(event: LogEvent, description: LogDescription): string {
  return [
    JSON.stringify(event),
    description.request,
    ...description.queries.flatMap(query => [query.label, query.value, ...query.options]),
    ...formatLogFilters(description.filters),
  ].join(' ').toLowerCase();
}

/** Construct formatters once per preference change, rather than once per cell. */
export function createLogTimeFormatter(settings: LogTimeSettings, showDate = true): (value: string) => string {
  const timeZone = settings.timeZone === 'utc' ? 'UTC' : undefined;
  const calendar = new Intl.DateTimeFormat('en-US', {
    year: 'numeric', month: '2-digit', day: '2-digit', timeZone,
  });
  const time = new Intl.DateTimeFormat(settings.timeFormat === 'h12' ? undefined : 'sv-SE', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: settings.timeFormat === 'h12', timeZone,
  });
  return value => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value || '—';
    const formattedTime = time.format(date);
    if (!showDate) return formattedTime;
    const parts = calendar.formatToParts(date);
    const part = (type: Intl.DateTimeFormatPartTypes) => parts.find(item => item.type === type)?.value ?? '';
    const dateParts = {
      ymd: [part('year'), part('month'), part('day')].join('-'),
      mdy: [part('month'), part('day'), part('year')].join('/'),
      dmy: [part('day'), part('month'), part('year')].join('/'),
    };
    return `${dateParts[settings.dateFormat]} ${formattedTime}`;
  };
}

export function finiteNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}
