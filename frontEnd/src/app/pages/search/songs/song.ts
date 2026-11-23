import { parseNonNegativeInteger } from '../../../shared/utils/number';

export interface SongCredit {
  id: number;
  names: string[];
  line_up_id: number;
  groups: SongCredit[] | null;
  members: SongCredit[] | null;
  type?: 'person' | 'group' | 'choir' | null;
  member_count?: number | null;
}

export interface AnimeListLinks {
  myanimelist: number | null;
  anidb: number | null;
  anilist: number | null;
  kitsu: number | null;
}

/** Mirrors the backend SongEntry response model. */
export interface Song {
  annId: number;
  annSongId: number;
  amqSongId: number;
  animeENName: string;
  animeJPName: string;
  animeAltName: string[];
  animeVintage: string | null;
  linked_ids: AnimeListLinks;
  animeType: string | null;
  animeCategory: string | null;
  songType: string;
  songName: string;
  songArtist: string;
  songComposer: string;
  songArranger: string;
  songDifficulty: number | null;
  songCategory: string | null;
  songLength: number | null;
  isDub: boolean | null;
  isRebroadcast: boolean | null;
  HQ: string | null;
  MQ: string | null;
  audio: string | null;
  artists: SongCredit[];
  composers: SongCredit[];
  arrangers: SongCredit[];
}

type SongPlaybackFields = Pick<Song, 'audio' | 'MQ' | 'HQ'>;

/**
 * Prefer the dedicated MP3, then fall back to the lower-bandwidth video files.
 * Keep this shared by playback controls and the player so they agree on which
 * songs can be played.
 */
export function getSongPlaybackSource(song: SongPlaybackFields): string | null {
  return song.audio || song.MQ || song.HQ || null;
}

export function hasSongPlaybackSource(song: SongPlaybackFields): boolean {
  return getSongPlaybackSource(song) !== null;
}

/** ANN song IDs are non-negative; the backend uses -1 for "missing". */
export function hasAnnSongId(song: Pick<Song, 'annSongId'>): boolean {
  return parseNonNegativeInteger(song.annSongId) !== null;
}
