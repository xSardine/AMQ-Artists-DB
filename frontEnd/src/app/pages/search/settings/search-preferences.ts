import type { StorageDefinition } from '../../../core/browser-storage.service';
import { objectValue } from '../../../core/storage-validation';

type PreferenceOption<Id extends string> = {
  id: Id;
  label: string;
};

export const SEARCH_MODE_OPTIONS = [
  {
    id: 'simple',
    label: 'Simple',
  },
  {
    id: 'advanced',
    label: 'Advanced',
  },
] as const satisfies readonly PreferenceOption<string>[];

export type SearchModePreference = typeof SEARCH_MODE_OPTIONS[number]['id'];

export const ANIME_TITLE_LANGUAGE_OPTIONS = [
  {
    id: 'EN',
    label: 'EN',
  },
  {
    id: 'JP',
    label: 'JP',
  },
] as const satisfies readonly PreferenceOption<string>[];

export type AnimeTitleLanguage = typeof ANIME_TITLE_LANGUAGE_OPTIONS[number]['id'];

export const RADIO_MODE_OPTIONS = [
  {
    id: 'none',
    label: 'None',
  },
  {
    id: 'repeat',
    label: 'Repeat',
  },
  {
    id: 'loop-all',
    label: 'Loop all',
  },
] as const satisfies readonly PreferenceOption<string>[];

export type RadioMode = typeof RADIO_MODE_OPTIONS[number]['id'];

type DistServerConfig = PreferenceOption<string> & {
  baseUrl: string;
};

export const DIST_SERVER_OPTIONS = [
  {
    id: 'nawdist',
    label: 'North America West',
    baseUrl: 'https://nawdist.animemusicquiz.com/',
  },
  {
    id: 'naedist',
    label: 'North America East',
    baseUrl: 'https://naedist.animemusicquiz.com/',
  },
  {
    id: 'eudist',
    label: 'Europe',
    baseUrl: 'https://eudist.animemusicquiz.com/',
  },
] as const satisfies readonly DistServerConfig[];

export type DistServerOption = typeof DIST_SERVER_OPTIONS[number];
export type DistServer = typeof DIST_SERVER_OPTIONS[number]['id'];

export type SearchPreferences = {
  searchMode: SearchModePreference;
  animeTitleLanguage: AnimeTitleLanguage;
  showAnimeLanguageToggle: boolean;
  showSongIds: boolean;
  showArtistIds: boolean;
  radioMode: RadioMode;
  distServer: DistServer;
};

export const DEFAULT_SEARCH_PREFERENCES: SearchPreferences = {
  searchMode: 'simple',
  animeTitleLanguage: 'JP',
  showAnimeLanguageToggle: true,
  showSongIds: false,
  showArtistIds: false,
  radioMode: 'none',
  distServer: 'naedist',
};

export const SEARCH_SETTINGS: StorageDefinition<SearchPreferences> = {
  key: 'anisongdb-search-settings',
  defaults: () => normalizeSearchPreferences({}),
  recover: value => normalizeSearchPreferences(objectValue(value)),
  parse(value) {
    const defaults = normalizeSearchPreferences({});
    const record = objectValue(value, Object.keys(defaults));
    const normalized = normalizeSearchPreferences(record);
    if (Object.entries(normalized).some(([key, expected]) => record[key] !== expected)) {
      throw new Error('Invalid search settings.');
    }
    return normalized;
  },
};

export function normalizeSearchPreferences(
  values: Record<string, unknown>,
): SearchPreferences {
  return {
    searchMode: isOptionId(SEARCH_MODE_OPTIONS, values['searchMode'])
      ? values['searchMode']
      : DEFAULT_SEARCH_PREFERENCES.searchMode,
    animeTitleLanguage: isOptionId(
      ANIME_TITLE_LANGUAGE_OPTIONS,
      values['animeTitleLanguage'],
    )
      ? values['animeTitleLanguage']
      : DEFAULT_SEARCH_PREFERENCES.animeTitleLanguage,
    showAnimeLanguageToggle: typeof values['showAnimeLanguageToggle'] === 'boolean'
      ? values['showAnimeLanguageToggle']
      : DEFAULT_SEARCH_PREFERENCES.showAnimeLanguageToggle,
    showSongIds: typeof values['showSongIds'] === 'boolean'
      ? values['showSongIds']
      : DEFAULT_SEARCH_PREFERENCES.showSongIds,
    showArtistIds: typeof values['showArtistIds'] === 'boolean'
      ? values['showArtistIds']
      : DEFAULT_SEARCH_PREFERENCES.showArtistIds,
    radioMode: isOptionId(RADIO_MODE_OPTIONS, values['radioMode'])
      ? values['radioMode']
      : DEFAULT_SEARCH_PREFERENCES.radioMode,
    distServer: isOptionId(DIST_SERVER_OPTIONS, values['distServer'])
      ? values['distServer']
      : DEFAULT_SEARCH_PREFERENCES.distServer,
  };
}

export function getDistServerOption(server: DistServer): DistServerOption {
  const option = DIST_SERVER_OPTIONS.find((candidate) => candidate.id === server);
  if (!option) throw new RangeError(`Unknown distribution server: ${server}`);
  return option;
}

function isOptionId<Id extends string>(
  options: readonly PreferenceOption<Id>[],
  value: unknown,
): value is Id {
  return typeof value === 'string'
    && options.some((option) => option.id === value);
}
