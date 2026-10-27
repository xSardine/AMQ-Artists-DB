import { compareSongsByAnnId } from '../songs/song-ordering';
import { compareSongTypes, formatSongLength, getBroadcastMetadata, parseAnimeSeason } from '../songs/song-metadata';
import type { AnimeTitleLanguage } from '../settings/search-preferences';
import { hasAnnSongId, type Song } from '../songs/song';

type SortableSongValue = string | number | boolean | null | undefined;

export type SongColumnReader<Value> = (
  song: Song,
  language: AnimeTitleLanguage,
) => Value;

export type SongColumnComparator = (
  left: Song,
  right: Song,
  language: AnimeTitleLanguage,
) => number;

export type SongColumnCellContext = {
  readonly song: Song;
  readonly rowIndex: number;
  readonly animeTitleLanguage: AnimeTitleLanguage;
};

export type SongColumnCellRenderer = (
  container: HTMLElement,
  context: SongColumnCellContext,
) => void | (() => void);

type SongColumnBase = {
  id: string;
  header: string;
  visibilityLabel?: string;
  defaultVisible: boolean;
  centered?: boolean;
  nowrap?: boolean;
  // Complete column comparison before the shared default tie-break chain.
  sort?: SongColumnComparator;
};

export type SongColumnDefinition = SongColumnBase & {
  // Cell value shown in the table.
  display?: SongColumnReader<string | number | null | undefined>;
  // Clipboard text value.
  copy?: SongColumnReader<string>;
  // Userscript-owned DOM renderer. Built-in columns use Angular templates.
  renderCell?: SongColumnCellRenderer;
};

export type CustomSongColumnDefinition = SongColumnBase & (
  | {
    display: SongColumnReader<string | number | null | undefined>;
    copy?: SongColumnReader<string>;
    renderCell?: never;
  }
  | {
    renderCell: SongColumnCellRenderer;
    display?: never;
    copy?: never;
  }
);

export type SongColumnPosition =
  | { before: string; after?: never }
  | { after: string; before?: never };

const getAnimeTitle: SongColumnReader<string> = (song, language) =>
  language === 'JP' ? song.animeJPName : song.animeENName;

const compareSongType: SongColumnComparator = (left, right) =>
  compareSongTypes(left.songType, right.songType);

const compareSongName: SongColumnComparator = (left, right) =>
  comparePrimitiveValues(left.songName, right.songName);

const compareAnimeTitle: SongColumnComparator = (left, right, language) =>
  comparePrimitiveValues(
    getAnimeTitle(left, language),
    getAnimeTitle(right, language),
  );

export const SONG_TABLE_COLUMNS: readonly SongColumnDefinition[] = [
  {
    id: 'info',
    header: 'Info',
    defaultVisible: true,
    centered: true,
  },
  {
    id: 'row-number',
    header: '#',
    visibilityLabel: 'Row Number',
    defaultVisible: false,
    centered: true,
  },
  {
    id: 'ann-id',
    header: 'ANN ID',
    defaultVisible: true,
    nowrap: true,
    display: (song) => song.annId,
    copy: (song) => String(song.annId),
    sort: compareSongsByAnnId,
  },
  {
    id: 'ann-song-id',
    header: 'ANN Song ID',
    defaultVisible: false,
    display: (song) => (hasAnnSongId(song) ? song.annSongId : '–'),
    copy: (song) => (hasAnnSongId(song) ? String(song.annSongId) : ''),
    sort: sortBy((song) => song.annSongId),
  },
  {
    id: 'amq-song-id',
    header: 'AMQ Song ID',
    defaultVisible: false,
    display: (song) => song.amqSongId,
    copy: (song) => String(song.amqSongId),
    sort: sortBy((song) => song.amqSongId),
  },
  {
    id: 'anime-lists',
    header: 'Anime Lists',
    defaultVisible: false,
    nowrap: true,
  },
  {
    id: 'season',
    header: 'Season',
    defaultVisible: true,
    display: (song) => getSeasonYearValue(song),
    copy: (song) => {
      const value = getSeasonYearValue(song);
      return value === '–' ? '' : value;
    },
    sort: sortBy(
      (song) => {
        return parseAnimeSeason(song.animeVintage)?.order ?? -1;
      },
      compareAnimeTitle,
      compareSongType,
    ),
  },
  {
    id: 'anime-type',
    header: 'Anime Type',
    defaultVisible: false,
    display: (song) => song.animeType || '–',
    copy: (song) => song.animeType || '',
    sort: sortBy((song) => song.animeType),
  },
  {
    id: 'anime',
    header: 'Anime',
    defaultVisible: true,
    display: getAnimeTitle,
    copy: getAnimeTitle,
    sort: sortBy(
      getAnimeTitle,
      compareSongType,
    ),
  },
  {
    id: 'broadcast',
    header: 'Broadcast',
    defaultVisible: false,
    nowrap: true,
    display: (song) => getBroadcastMetadata(song).label,
    copy: (song) => getBroadcastMetadata(song).label,
    sort: sortBy((song) => getBroadcastMetadata(song).order),
  },
  {
    id: 'song-type',
    header: 'Song Type',
    defaultVisible: true,
    nowrap: true,
    display: (song) => song.songType || '–',
    copy: (song) => song.songType || '',
    sort: compareSongType,
  },
  {
    id: 'performance',
    header: 'Performance',
    defaultVisible: false,
    display: (song) => song.songCategory || '–',
    copy: (song) => song.songCategory || '',
    sort: sortBy((song) => song.songCategory),
  },
  {
    id: 'song-name',
    header: 'Song Name',
    defaultVisible: true,
    display: (song) => song.songName || '–',
    copy: (song) => song.songName || '',
    sort: sortBy((song) => song.songName),
  },
  {
    id: 'artist',
    header: 'Artist',
    defaultVisible: true,
    display: (song) => song.songArtist || '–',
    copy: (song) => song.songArtist || '',
    sort: sortBy(
      (song) => song.songArtist,
      compareSongName,
    ),
  },
  {
    id: 'composer',
    header: 'Composer',
    defaultVisible: false,
    display: (song) => song.songComposer || '–',
    copy: (song) => song.songComposer || '',
    sort: sortBy(
      (song) => song.songComposer,
      compareSongName,
    ),
  },
  {
    id: 'arranger',
    header: 'Arranger',
    defaultVisible: false,
    display: (song) => song.songArranger || '–',
    copy: (song) => song.songArranger || '',
    sort: sortBy(
      (song) => song.songArranger,
      compareSongName,
    ),
  },
  {
    id: 'difficulty',
    header: 'Difficulty',
    defaultVisible: false,
    display: (song) => song.songDifficulty != null ? `${song.songDifficulty}%` : '–',
    copy: (song) => String(song.songDifficulty ?? ''),
    sort: sortBy((song) => Number(song.songDifficulty ?? -1)),
  },
  {
    id: 'length',
    header: 'Length',
    defaultVisible: false,
    display: (song) => formatSongLength(song.songLength) || '–',
    copy: (song) => formatSongLength(song.songLength) || '',
    sort: sortBy((song) => Number(song.songLength ?? -1)),
  },
  {
    id: 'song-links',
    header: 'Song Links',
    defaultVisible: false,
    nowrap: true,
  },
  {
    id: 'play-audio',
    header: 'Play',
    visibilityLabel: 'Play Audio',
    defaultVisible: true,
    centered: true,
  },
  {
    id: 'add-playlist',
    header: 'Add',
    visibilityLabel: 'Add to Playlist',
    defaultVisible: false,
    centered: true,
  },
  {
    id: 'move-row',
    header: 'Move',
    visibilityLabel: 'Move Row',
    defaultVisible: false,
    centered: true,
  },
  {
    id: 'delete-row',
    header: 'Del',
    visibilityLabel: 'Delete Row',
    defaultVisible: true,
    centered: true,
  },
];

function getSeasonYearValue(song: Song): string {
  return parseAnimeSeason(song.animeVintage)?.label
    ?? song.animeVintage
    ?? '–';
}

export function getColumnDisplayValue(
  song: Song,
  column: SongColumnDefinition,
  language: AnimeTitleLanguage,
): string | number {
  return column.display?.(song, language) ?? '–';
}

export function getColumnCopyValue(
  song: Song,
  column: SongColumnDefinition,
  language: AnimeTitleLanguage,
): string {
  return column.copy?.(song, language) ?? '';
}

export function comparePrimitiveValues(
  left: SortableSongValue,
  right: SortableSongValue,
): number {
  if (left === right) return 0;
  if (left === undefined || left === null) return 1;
  if (right === undefined || right === null) return -1;
  if (typeof left === 'number' && typeof right === 'number') return left < right ? -1 : 1;
  return String(left).localeCompare(String(right), undefined, {
    numeric: true,
    sensitivity: 'base',
  });
}

function sortBy(
  read: SongColumnReader<SortableSongValue>,
  ...tieBreaks: SongColumnComparator[]
): SongColumnComparator {
  return (left, right, language) => {
    let comparison = comparePrimitiveValues(
      read(left, language),
      read(right, language),
    );

    for (const tieBreak of tieBreaks) {
      if (comparison !== 0) break;
      comparison = tieBreak(left, right, language);
    }

    return comparison;
  };
}

export function compareSongsByColumn(
  left: Song,
  right: Song,
  column: SongColumnDefinition,
  language: AnimeTitleLanguage,
): number {
  if (!column.sort) return 0;

  return column.sort(left, right, language)
    || compareSongsByAnnId(left, right);
}
