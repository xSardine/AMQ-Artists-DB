import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { Subscription } from 'rxjs';
import { ApiClient, errorMessage } from '../../../core/api-client.service';
import type { Song } from '../songs/song';
import { NotificationService } from '../../../shared/feedback/notification.service';
import { formatSongCount } from '../songs/song-metadata';
import { reorderSongsByAnnSongIds, sortSongsByDefault } from '../songs/song-ordering';
import { SongWorkspaceStore } from '../songs/song-workspace.store';
import { DEFAULT_CREDIT_OPTIONS, type SearchCommand, type SongId } from './search-command';
import { searchDownloadFileName } from './search-download';

const SEARCH_ENDPOINTS: Record<SearchCommand['kind'], string> = {
  'initial-random': '/api/get_50_random_songs',
  'random': '/api/get_n_random_songs',
  'general': '/api/search_request',
  'season': '/api/season_request',
  'ann-ids': '/api/ann_ids_request',
  'mal-ids': '/api/mal_ids_request',
  'anilist-ids': '/api/anilist_ids_request',
  'kitsu-ids': '/api/kitsu_ids_request',
  'anidb-ids': '/api/anidb_ids_request',
  'ann-song-ids': '/api/ann_song_ids_request',
  'amq-song-ids': '/api/amq_song_ids_request',
  'artist-ids': '/api/artist_ids_request',
  'composer-ids': '/api/composer_ids_request',
};

type PlaylistLoadSource = 'import' | 'saved';

type PlaylistLoad = {
  annSongIds: number[];
  source: PlaylistLoadSource;
};

export type SearchRequestState =
  | { status: 'idle' }
  | { status: 'loading'; command: SearchCommand }
  | { status: 'error'; message: string };

/**
 * Owns search request execution, cancellation, and errors. Successful results
 * are committed to SongWorkspaceStore, which owns the current song collection.
 */
@Injectable()
export class SearchService {
  private readonly api = inject(ApiClient);
  private readonly workspace = inject(SongWorkspaceStore);
  private readonly notifications = inject(NotificationService);
  private readonly destroyRef = inject(DestroyRef);
  // The key prevents an identical in-flight request from being restarted.
  // Completed searches are not cached or deduplicated.
  private activeSearch: { key: string; subscription: Subscription } | null = null;
  private readonly requestStateSignal = signal<SearchRequestState>({ status: 'idle' });

  readonly requestState = this.requestStateSignal.asReadonly();
  readonly searchError = computed(() => {
    const state = this.requestStateSignal();
    return state.status === 'error' ? state.message : null;
  });

  constructor() {
    this.destroyRef.onDestroy(() => this.cancel());
  }

  startInitialSearch(): boolean {
    return this.runSearch({ kind: 'initial-random' });
  }

  cancel(): void {
    this.cancelActiveSearch();
    if (this.requestStateSignal().status === 'loading') {
      this.requestStateSignal.set({ status: 'idle' });
    }
  }

  runSearch(command: SearchCommand): boolean {
    if (this.destroyRef.destroyed) return false;
    const searchKey = JSON.stringify(command);
    // Do not restart an identical request that is already in flight.
    if (searchKey === this.activeSearch?.key) return false;
    this.execute(command, null, searchKey);
    return true;
  }

  searchSeason(season: string): boolean {
    return this.runSearch({ kind: 'season', body: { season } });
  }

  searchAnnIds(ids: SongId[]): boolean {
    return this.runSearch({ kind: 'ann-ids', body: { ann_ids: ids } });
  }

  searchAnnSongIds(ids: SongId[]): boolean {
    return this.runSearch({ kind: 'ann-song-ids', body: { ann_song_ids: ids } });
  }

  loadPlaylist(ids: number[], source: PlaylistLoadSource): void {
    if (this.destroyRef.destroyed) return;
    if (!ids.length) {
      // Empty playlists are valid, but the ID-search API correctly rejects an
      // empty ID list. Apply the empty result locally instead of presenting a
      // normal playlist load as a request-validation failure.
      this.cancelActiveSearch();
      this.requestStateSignal.set({ status: 'idle' });
      this.notifyPlaylistLoad(source, 0, 0);
      this.workspace.replace([], null, 'Playlist_SongList.json');
      return;
    }

    this.execute({ kind: 'ann-song-ids', body: { ann_song_ids: ids } }, {
      annSongIds: [...ids],
      source,
    });
  }

  searchAmqSongIds(ids: SongId[]): boolean {
    return this.runSearch({ kind: 'amq-song-ids', body: { amq_song_ids: ids } });
  }

  searchArtistIds(artistIds: number[]): boolean {
    return this.runSearch({
      kind: 'artist-ids',
      body: {
        artist_ids: artistIds,
        ...DEFAULT_CREDIT_OPTIONS,
      },
    });
  }

  searchComposerIds(composerIds: number[]): boolean {
    return this.runSearch({
      kind: 'composer-ids',
      body: { composer_ids: composerIds, arrangement: true },
    });
  }

  private execute(
    command: SearchCommand,
    playlistLoad: PlaylistLoad | null,
    searchKey = JSON.stringify(command),
  ): void {
    const downloadFileName = playlistLoad ? 'Playlist_SongList.json' : searchDownloadFileName(command);
    const request = this.api.request<Song[]>(SEARCH_ENDPOINTS[command.kind], {
      method: 'POST',
      body: 'body' in command ? command.body : {},
      headers: { 'X-Client-Id': 'AnisongDB' },
    });
    this.cancelActiveSearch();
    this.requestStateSignal.set({ status: 'loading', command });

    const subscription = request.subscribe({
      next: (results) => {
        const nextSongList = playlistLoad
          ? reorderSongsByAnnSongIds(results, playlistLoad.annSongIds)
          : sortSongsByDefault(results);

        if (playlistLoad) {
          this.notifyPlaylistLoad(
            playlistLoad.source,
            new Set(playlistLoad.annSongIds).size,
            nextSongList.length,
          );
        }

        this.workspace.replace(
          nextSongList,
          playlistLoad ? null : { column: 'ann-id', ascending: true },
          downloadFileName,
        );
      },
      error: (error: unknown) => {
        this.requestStateSignal.set({
          status: 'error',
          message: errorMessage(error),
        });
        console.error('Search failed:', error);
        this.finishSearch();
      },
      complete: () => {
        this.requestStateSignal.set({ status: 'idle' });
        this.finishSearch();
      },
    });
    this.activeSearch = subscription.closed ? null : { key: searchKey, subscription };
  }

  private cancelActiveSearch(): void {
    // HttpClient observables honor RxJS unsubscription. Once unsubscribed, the
    // old subscriber cannot deliver next/error/complete, so a separate request
    // generation counter or stale-callback guard would be redundant here.
    this.activeSearch?.subscription.unsubscribe();
    this.activeSearch = null;
  }

  private finishSearch(): void {
    this.activeSearch = null;
  }

  private notifyPlaylistLoad(
    source: PlaylistLoadSource,
    requestedCount: number,
    loadedCount: number,
  ): void {
    if (loadedCount < requestedCount) {
      this.notifications.show(`Loaded ${loadedCount} of ${requestedCount} songs.`);
    } else if (source === 'import') {
      this.notifications.show(`Loaded ${formatSongCount(loadedCount)} into the table.`);
    }
  }
}
