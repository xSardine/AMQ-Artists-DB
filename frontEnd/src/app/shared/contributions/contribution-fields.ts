import type { ContributionOperation } from './contribution-types';

export const FIELD_DEFINITIONS = {
  anime_original_title: {
    kind: 'anime',
    label: 'Original anime title',
    valueType: 'text',
  },
  anime_original_alias: {
    kind: 'anime',
    label: 'Original anime alias',
    valueType: 'aliases',
  },
  artist_original_alias: {
    kind: 'artist',
    label: 'Original artist alias',
    valueType: 'aliases',
  },
  artist_ann_id: {
    kind: 'artist',
    label: 'ANN artist ID',
    valueType: 'integer',
    profilePrefix: 'https://www.animenewsnetwork.com/encyclopedia/people.php?id=',
  },
  artist_mal_id: {
    kind: 'artist',
    label: 'MyAnimeList artist ID',
    valueType: 'integer',
    profilePrefix: 'https://myanimelist.net/people/',
  },
  artist_anilist_id: {
    kind: 'artist',
    label: 'AniList artist ID',
    valueType: 'integer',
    profilePrefix: 'https://anilist.co/staff/',
  },
  song_original_title: {
    kind: 'song',
    label: 'Original song title',
    valueType: 'text',
  },
  song_original_performer_credit: {
    kind: 'song',
    label: 'Original performer credit',
    valueType: 'text',
  },
  song_original_composer_credit: {
    kind: 'song',
    label: 'Original composer credit',
    valueType: 'text',
  },
  song_original_arranger_credit: {
    kind: 'song',
    label: 'Original arranger credit',
    valueType: 'text',
  },
} as const;

export type ContributionField = keyof typeof FIELD_DEFINITIONS;

export const FIELD_LABELS = Object.fromEntries(
  Object.entries(FIELD_DEFINITIONS).map(([key, field]) => [key, field.label]),
) as Record<ContributionField, string>;

const ALIAS_OPERATIONS = ['add_alias', 'replace_alias', 'remove_alias'] as const;
const VALUE_OPERATIONS = ['set', 'clear'] as const;

export function allowedOperations(field: ContributionField): readonly ContributionOperation[] {
  return FIELD_DEFINITIONS[field].valueType === 'aliases' ? ALIAS_OPERATIONS : VALUE_OPERATIONS;
}

export function defaultOperation(field: ContributionField): ContributionOperation {
  return FIELD_DEFINITIONS[field].valueType === 'aliases' ? 'add_alias' : 'set';
}

export function isArtistId(field: ContributionField): boolean {
  return FIELD_DEFINITIONS[field].valueType === 'integer';
}

export function normalizeValue(field: ContributionField, value: unknown): string | number {
  if (isArtistId(field)) {
    if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 1) {
      throw new Error('Enter a positive integer artist ID.');
    }
    return value;
  }
  if (typeof value !== 'string'
    || !value.trim()
    || value.trim().length > 500
    || /[\u0000-\u001f]/.test(value)) {
    throw new Error('Enter a nonempty, single-line name (up to 500 characters).');
  }
  return value.trim();
}

export function profileUrl(field: ContributionField, value: unknown): string | null {
  const definition = FIELD_DEFINITIONS[field];
  if (!('profilePrefix' in definition)
    || typeof value !== 'number'
    || !Number.isSafeInteger(value)
    || value < 1) {
    return null;
  }

  return definition.profilePrefix + value;
}
