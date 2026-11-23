import { inject, Injectable } from '@angular/core';
import { BrowserStorage } from '../../../core/browser-storage.service';
import { objectValue, textValue } from '../../../core/storage-validation';
import { PLAYLIST_STORAGE, SavedPlaylists } from '../playlist/playlist-storage';
import { TABLE_SETTINGS, TableSettings } from '../song-table/table-settings';
import { SEARCH_SETTINGS, SearchPreferences } from './search-preferences';
import { downloadJsonFile, readJsonFile } from '../../../shared/utils/json-file';

interface SearchBackup {
  format: 'anisongdb-search-backup';
  exportedAt: string;
  data: {
    search: SearchPreferences;
    table: TableSettings;
    playlists: SavedPlaylists;
  };
}

export type SearchDataScope = 'preferences' | 'table' | 'playlists';

@Injectable()
export class SearchBackupService {
  private readonly storage = inject(BrowserStorage);
  private readonly search = this.storage.record(SEARCH_SETTINGS);
  private readonly table = this.storage.record(TABLE_SETTINGS);
  private readonly playlists = this.storage.record(PLAYLIST_STORAGE);

  export(): void {
    const backup: SearchBackup = {
      format: 'anisongdb-search-backup',
      exportedAt: new Date().toISOString(),
      data: { search: this.search.value(), table: this.table.value(), playlists: this.playlists.value() },
    };
    downloadJsonFile(`anisongdb-search-${backup.exportedAt.slice(0, 10)}.json`, backup, 2);
  }

  async read(file: File): Promise<SearchBackup> {
    const backup = objectValue(await readJsonFile(file), ['format', 'exportedAt', 'data']);
    if (backup['format'] !== 'anisongdb-search-backup') throw new Error('That is not a search backup.');
    const date = textValue(backup['exportedAt'], 50, false);
    if (!Number.isFinite(Date.parse(date))) throw new Error('Invalid backup date.');
    const data = objectValue(backup['data'], ['search', 'table', 'playlists']);
    return {
      format: 'anisongdb-search-backup',
      exportedAt: date,
      data: {
        search: SEARCH_SETTINGS.parse(data['search']),
        table: TABLE_SETTINGS.parse(data['table']),
        playlists: PLAYLIST_STORAGE.parse(data['playlists']),
      },
    };
  }

  async import(backup: SearchBackup): Promise<void> {
    await this.storage.replace([
      this.search.replacement(backup.data.search),
      this.table.replacement(backup.data.table),
      this.playlists.replacement(backup.data.playlists),
    ]);
  }

  async reset(scope: SearchDataScope): Promise<void> {
    const replacements = {
      preferences: () => this.search.replacement(SEARCH_SETTINGS.defaults()),
      table: () => this.table.replacement(TABLE_SETTINGS.defaults()),
      playlists: () => this.playlists.replacement(PLAYLIST_STORAGE.defaults()),
    };
    await this.storage.replace([replacements[scope]()]);
  }
}
