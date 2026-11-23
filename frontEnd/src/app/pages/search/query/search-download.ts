import { sanitizeFileNameSegment } from '../../../shared/utils/json-file';
import type { SearchCommand, SongId } from './search-command';

/** Describes the submitted request independently of later form edits. */
export function searchDownloadFileName(command: SearchCommand): string {
  switch (command.kind) {
    case 'initial-random':
      return 'SongList.json';
    case 'random':
      return fileName(['Random', String(command.body.n)]);
    case 'season':
      return fileName([command.body.season]);
    case 'general': {
      const filters = [
        command.body.anime_search_filter,
        command.body.song_name_search_filter,
        command.body.artist_search_filter,
        command.body.composer_search_filter,
      ];
      const terms = filters.flatMap(filter => filter ? [filter.search] : []);
      return fileName([...new Set(terms)]);
    }
    case 'ann-ids':
      return idFileName('ANN-ID', command.body.ann_ids);
    case 'mal-ids':
      return idFileName('MAL-ID', command.body.mal_ids);
    case 'anilist-ids':
      return idFileName('AniList-ID', command.body.anilist_ids);
    case 'kitsu-ids':
      return idFileName('Kitsu-ID', command.body.kitsu_ids);
    case 'anidb-ids':
      return idFileName('AniDB-ID', command.body.anidb_ids);
    case 'ann-song-ids':
      return idFileName('ANN-Song-ID', command.body.ann_song_ids);
    case 'amq-song-ids':
      return idFileName('AMQ-Song-ID', command.body.amq_song_ids);
    case 'artist-ids':
      return idFileName('Artist-ID', command.body.artist_ids);
    case 'composer-ids':
      return idFileName('Composer-ID', command.body.composer_ids);
  }
}

function idFileName(label: string, ids: readonly SongId[]): string {
  // Large ID lookups should still produce a reasonably short filename.
  const terms = ids.slice(0, 5).map(String);
  if (ids.length > 5) terms.push(`${ids.length}-ids`);
  return fileName([label, ...terms]);
}

function fileName(terms: readonly string[]): string {
  const segments = terms.map(sanitizeFileNameSegment).filter(Boolean);
  return [...segments, 'SongList'].join('_') + '.json';
}
