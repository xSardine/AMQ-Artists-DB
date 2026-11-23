type ParsedAnimeSeason = {
  label: string;
  order: number;
};

type ParsedSongType = {
  number: number;
  shortLabel: string;
  order: number;
};

const ANIME_SEASONS = {
  winter: { label: 'Winter', index: 0 },
  spring: { label: 'Spring', index: 1 },
  summer: { label: 'Summer', index: 2 },
  fall: { label: 'Fall', index: 3 },
} as const;

const BROADCAST_METADATA = [
  { label: 'Normal', order: 0 },
  { label: 'Dub', order: 1 },
  { label: 'Rebroadcast', order: 2 },
  { label: 'Dub, Rebroadcast', order: 3 },
] as const;

export function parseAnimeSeason(value: unknown): ParsedAnimeSeason | null {
  const match = String(value ?? '').trim().match(
    /^(winter|spring|summer|fall)\s*(\d{4})$/i,
  );
  if (!match) return null;

  const season = ANIME_SEASONS[
    match[1].toLowerCase() as keyof typeof ANIME_SEASONS
  ];
  const year = Number(match[2]);
  return {
    label: `${season.label} ${year}`,
    order: year * 4 + season.index,
  };
}

export function parseSongType(value: unknown): ParsedSongType {
  const text = String(value ?? '').trim();
  const numbered = /^(opening|ending)(?:\s+song)?(?:\s+(\d+))?$/i.exec(text);
  if (numbered) {
    const opening = numbered[1].toLowerCase() === 'opening';
    return {
      number: Number(numbered[2] ?? 0),
      shortLabel: opening ? 'OP' : 'ED',
      order: opening ? 0 : 1,
    };
  }

  if (/^insert(?:\s+song)?$/i.test(text)) {
    return {
      number: 0,
      shortLabel: 'IN',
      order: 2,
    };
  }

  return {
    number: 0,
    shortLabel: text || '(none)',
    order: 3,
  };
}

export function getBroadcastMetadata(song: {
  isDub?: boolean | null;
  isRebroadcast?: boolean | null;
}): typeof BROADCAST_METADATA[number] {
  const index = Number(!!song.isDub) + 2 * Number(!!song.isRebroadcast);
  return BROADCAST_METADATA[index];
}

/** Compares song types: Opening, then Ending, then Insert Song, then unknown. */
export function compareSongTypes(left: unknown, right: unknown): number {
  const leftMetadata = parseSongType(left);
  const rightMetadata = parseSongType(right);
  return leftMetadata.order - rightMetadata.order
    || leftMetadata.number - rightMetadata.number;
}

export function formatSongLength(
  length: string | number | null | undefined,
): string {
  if (length == null || length === '') return '';

  const seconds = Math.round(Number(length));
  if (!Number.isFinite(seconds) || seconds < 0) return '';

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = String(seconds % 60).padStart(2, '0');
  return `${minutes}:${remainingSeconds}`;
}

export function formatSongCount(count: number): string {
  return `${count} song${count === 1 ? '' : 's'}`;
}
