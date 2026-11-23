import { StorageDefinition } from '../../../core/browser-storage.service';
import { integerValue, objectValue, optionValue, recoverValue, textValue, uniqueValues } from '../../../core/storage-validation';
import { DEFAULT_PLAYLIST_SORT, PLAYLIST_SORT_OPTIONS, Playlist, PlaylistSort } from './playlist';

export const PLAYLIST_MAX_SONGS = 500;

export interface SavedPlaylists {
  items: Playlist[];
  sort: PlaylistSort;
}

function playlistValue(value: unknown): Playlist {
  const playlist = objectValue(value, ['id', 'name', 'createdOn', 'annSongIds']);
  const date = textValue(playlist['createdOn'], 50, false);
  if (!Number.isFinite(Date.parse(date))) throw new Error('Invalid playlist date.');
  const ids = playlist['annSongIds'];
  if (!Array.isArray(ids) || ids.length > PLAYLIST_MAX_SONGS) throw new Error('Invalid playlist songs.');
  return {
    id: textValue(playlist['id'], 100, false),
    name: textValue(playlist['name'], 100, false),
    createdOn: date,
    annSongIds: uniqueValues(ids.map(id => integerValue(id))),
  };
}

function recoverPlaylist(value: unknown): Playlist {
  const playlist = objectValue(value);
  const ids = Array.isArray(playlist['annSongIds']) ? playlist['annSongIds'] : [];
  const validIds = ids.flatMap(id => {
    const valid = recoverValue(id, integerValue, null);
    return valid === null ? [] : [valid];
  });
  return playlistValue({
    id: playlist['id'],
    name: playlist['name'],
    createdOn: playlist['createdOn'],
    annSongIds: [...new Set(validIds)].slice(0, PLAYLIST_MAX_SONGS),
  });
}

export const PLAYLIST_STORAGE: StorageDefinition<SavedPlaylists> = {
  key: 'anisongdb-playlists',
  defaults: () => ({ items: [], sort: DEFAULT_PLAYLIST_SORT }),
  recover(value) {
    const record = objectValue(value);
    const savedItems = Array.isArray(record['items']) ? record['items'] : [];
    const seen = new Set<string>();
    const items = savedItems.flatMap(value => {
      const item = recoverValue(value, recoverPlaylist, null);
      if (!item || seen.has(item.id)) return [];
      seen.add(item.id);
      return [item];
    });
    const sort = recoverValue(
      record['sort'],
      value => optionValue(value, PLAYLIST_SORT_OPTIONS.map(option => option.value)),
      DEFAULT_PLAYLIST_SORT,
    );
    return { items, sort };
  },
  parse(value) {
    const record = objectValue(value, ['items', 'sort']);
    if (!Array.isArray(record['items'])) throw new Error('Invalid playlists.');
    const items = record['items'].map(playlistValue);
    uniqueValues(items.map(item => item.id));
    return { items, sort: optionValue(record['sort'], PLAYLIST_SORT_OPTIONS.map(option => option.value)) };
  },
};
