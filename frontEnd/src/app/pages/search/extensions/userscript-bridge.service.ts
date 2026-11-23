import { DestroyRef, effect, inject, Injectable, Injector, untracked } from '@angular/core';
import { AudioPlaybackService } from '../audio/audio-playback.service';
import { BrowserStorage } from '../../../core/browser-storage.service';
import { SearchModalService } from '../search-modal.service';
import { NotificationService } from '../../../shared/feedback/notification.service';
import { RankedStatusService } from '../ranked-status.service';
import { SearchPreferencesService } from '../settings/search-preferences.service';
import { PlaylistService } from '../playlist/playlist.service';
import { SearchService } from '../query/search.service';
import { SearchSettingsTabRegistryService } from '../settings/search-settings-tab-registry.service';
import { SongWorkspaceStore } from '../songs/song-workspace.store';
import { SongTableController } from '../song-table/song-table.controller';

/**
 * Publishes a deliberately thin userscript bridge over raw Angular services.
 */
@Injectable()
export class UserscriptBridgeService {
  private readonly watchers = new Set<() => void>();
  private readonly injector = inject(Injector);
  private readonly destroyRef = inject(DestroyRef);

  private readonly services = Object.freeze({
    playback: inject(AudioPlaybackService),
    modals: inject(SearchModalService),
    notifications: inject(NotificationService),
    playlists: inject(PlaylistService),
    preferences: inject(SearchPreferencesService),
    rankedStatus: inject(RankedStatusService),
    searches: inject(SearchService),
    settingsTabs: inject(SearchSettingsTabRegistryService),
    storage: inject(BrowserStorage),
    table: inject(SongTableController),
    workspace: inject(SongWorkspaceStore),
  });

  readonly api = Object.freeze({
    services: this.services,
    watch: <T>(
      read: () => T,
      listener: (value: T) => void,
    ) => this.watch(read, listener),
  });

  constructor() {
    window.AnisongDB = this.api;
    this.destroyRef.onDestroy(() => {
      this.disposeWatchers();
      if (window.AnisongDB === this.api) delete window.AnisongDB;
    });
  }

  private watch<T>(
    read: () => T,
    listener: (value: T) => void,
  ): () => void {
    if (this.destroyRef.destroyed) return () => {};

    const watcher = effect(() => {
      const value = read();
      untracked(() => {
        try {
          listener(value);
        } catch (error) {
          console.error('An AnisongDB userscript watcher failed.', error);
        }
      });
    }, { injector: this.injector });

    const dispose = () => {
      watcher.destroy();
      this.watchers.delete(dispose);
    };
    this.watchers.add(dispose);
    return dispose;
  }

  private disposeWatchers(): void {
    for (const dispose of [...this.watchers]) dispose();
  }
}

declare global {
  interface Window {
    AnisongDB?: UserscriptBridgeService['api'];
  }
}
