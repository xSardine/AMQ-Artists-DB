import type { Song } from '../songs/song';
import type { AnimeTitleLanguage } from '../settings/search-preferences';
import { formatSongLength, getBroadcastMetadata, parseSongType } from '../songs/song-metadata';
import { collectPersonIds } from './song-credits';

export type StatBreakdownEntry = {
  label: string;
  count: number;
  percent: number;
};

type StatRankingEntry = {
  key: number;
  label: string;
  count: number;
};

type TableStats = {
  songCount: number;
  uniqueAnime: number;
  uniqueArtists: number;
  avgDifficulty: number;
  avgLength: number | null;
  animeTypeBreakdown: StatBreakdownEntry[];
  songTypeBreakdown: StatBreakdownEntry[];
  broadcastBreakdown: StatBreakdownEntry[];
  performanceBreakdown: StatBreakdownEntry[];
  topAnime: StatRankingEntry[];
  topArtists: StatRankingEntry[];
  difficultyBreakdown: StatBreakdownEntry[];
};

const EMPTY_TABLE_STATS: TableStats = {
  songCount: 0,
  uniqueAnime: 0,
  uniqueArtists: 0,
  avgDifficulty: 0,
  avgLength: null,
  animeTypeBreakdown: [],
  songTypeBreakdown: [],
  broadcastBreakdown: [],
  performanceBreakdown: [],
  topAnime: [],
  topArtists: [],
  difficultyBreakdown: [],
};

const SONG_TYPE_SORT_ORDER = ['OP', 'ED', 'IN'];
const BROADCAST_SORT_ORDER = ['Normal', 'Dub', 'Rebroadcast', 'Dub, Rebroadcast'];
const PERFORMANCE_SORT_ORDER = ['Standard', 'Character', 'Chanting', 'Instrumental', 'Other'];
const ANIME_TYPE_SORT_ORDER = ['TV', 'Movie', 'OVA', 'ONA', 'Special', 'Other'];
const DIFFICULTY_BUCKET_LABELS = [
  '0–9',
  '10–19',
  '20–29',
  '30–39',
  '40–49',
  '50–59',
  '60–69',
  '70–79',
  '80–89',
  '90–100',
];

export function formatAvgLength(seconds: number | null): string {
  return seconds == null ? '—' : formatSongLength(seconds) || '—';
}

export function computeTableStats(
  songs: readonly Song[] | null | undefined,
  animeTitleLanguage: AnimeTitleLanguage = 'JP',
): TableStats {
  if (!songs?.length) return { ...EMPTY_TABLE_STATS };

  const animeIds = new Set<number>();
  const artistIds = new Set<number>();
  const animeTypeCounts: Record<string, number> = {};
  const songTypeCounts: Record<string, number> = {};
  const broadcastCounts: Record<string, number> = {};
  const performanceCounts: Record<string, number> = {};
  const lengths: number[] = [];
  const difficulties: number[] = [];
  const animeCounts = new Map<number, StatRankingEntry>();
  const artistCounts = new Map<number, StatRankingEntry>();

  for (const song of songs) {
    if (song.annId != null) animeIds.add(song.annId);
    for (const artistId of collectPersonIds(song.artists)) artistIds.add(artistId);

    const animeLabel = animeTitleLanguage === 'JP' ? song.animeJPName : song.animeENName;
    incrementRanking(animeCounts, song.annId, animeLabel || '(none)');

    const artistsInSong = new Set<number>();
    for (const artist of song.artists ?? []) {
      if (artistsInSong.has(artist.id)) continue;
      artistsInSong.add(artist.id);
      incrementRanking(
        artistCounts,
        artist.id,
        artist.names?.find((name) => name.trim())?.trim() || '(none)',
      );
    }

    incrementCount(animeTypeCounts, song.animeType);
    incrementCount(songTypeCounts, parseSongType(song.songType).shortLabel);
    incrementCount(broadcastCounts, getBroadcastMetadata(song).label);
    incrementCount(performanceCounts, song.songCategory);

    const length = Number(song.songLength);
    if (song.songLength != null && Number.isFinite(length)) lengths.push(length);

    const difficulty = Number(song.songDifficulty);
    if (Number.isFinite(difficulty) && difficulty > 0) difficulties.push(difficulty);
  }

  const songCount = songs.length;
  return {
    songCount,
    uniqueAnime: animeIds.size,
    uniqueArtists: artistIds.size,
    avgDifficulty: difficulties.length ? average(difficulties) : 0,
    avgLength: lengths.length ? average(lengths) : null,
    songTypeBreakdown: buildBreakdown(songTypeCounts, songCount, SONG_TYPE_SORT_ORDER),
    broadcastBreakdown: buildBreakdown(broadcastCounts, songCount, BROADCAST_SORT_ORDER),
    performanceBreakdown: buildBreakdown(
      performanceCounts,
      songCount,
      PERFORMANCE_SORT_ORDER,
    ),
    animeTypeBreakdown: buildBreakdown(animeTypeCounts, songCount, ANIME_TYPE_SORT_ORDER),
    topAnime: topRankings(animeCounts),
    topArtists: topRankings(artistCounts),
    difficultyBreakdown: buildDifficultyBreakdown(difficulties),
  };
}

function average(values: readonly number[]): number {
  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1));
}

function incrementCount(counts: Record<string, number>, value: string | null | undefined): void {
  const label = value?.trim() || '(none)';
  counts[label] = (counts[label] ?? 0) + 1;
}

function incrementRanking(
  rankings: Map<number, StatRankingEntry>,
  key: number,
  label: string,
): void {
  const existing = rankings.get(key);
  if (existing) existing.count += 1;
  else rankings.set(key, { key, label, count: 1 });
}

function buildBreakdown(
  counts: Record<string, number>,
  total: number,
  sortLabels?: readonly string[],
): StatBreakdownEntry[] {
  const entries = Object.entries(counts).map(([label, count]) => ({
    label,
    count,
    percent: total ? Number(((count / total) * 100).toFixed(1)) : 0,
  }));

  return entries.sort((left, right) => {
    if (!sortLabels) return left.label.localeCompare(right.label);
    const leftIndex = sortLabels.indexOf(left.label);
    const rightIndex = sortLabels.indexOf(right.label);
    const leftRank = leftIndex < 0 ? sortLabels.length + 1 : leftIndex;
    const rightRank = rightIndex < 0 ? sortLabels.length + 1 : rightIndex;
    return leftRank - rightRank || left.label.localeCompare(right.label);
  });
}

function topRankings(rankings: Map<number, StatRankingEntry>): StatRankingEntry[] {
  return [...rankings.values()]
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))
    .slice(0, 10);
}

function buildDifficultyBreakdown(difficulties: readonly number[]): StatBreakdownEntry[] {
  const counts = DIFFICULTY_BUCKET_LABELS.map((label) => ({ label, count: 0 }));
  for (const difficulty of difficulties) {
    counts[Math.min(9, Math.floor(difficulty / 10))].count += 1;
  }
  return counts.map(({ label, count }) => ({
    label,
    count,
    percent: difficulties.length
      ? Number(((count / difficulties.length) * 100).toFixed(1))
      : 0,
  }));
}
