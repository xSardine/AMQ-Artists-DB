import { computed, inject, Injectable, signal } from '@angular/core';
import { BrowserStorage } from '../../../core/browser-storage.service';
import { PLAYLIST_STORAGE, PLAYLIST_MAX_SONGS } from './playlist-storage';
export { PLAYLIST_MAX_SONGS } from './playlist-storage';
import { parseNonNegativeInteger } from '../../../shared/utils/number';
import { DEFAULT_PLAYLIST_SORT, parsePlaylistSort, sortPlaylists, type Playlist, type PlaylistAddResult, type PlaylistAppendResult, type PlaylistToggleResult } from './playlist';


/** Notification texts for toggle results; results without user feedback are omitted. */
export const PLAYLIST_TOGGLE_MESSAGES: Partial<Record<PlaylistToggleResult, string>> = {
  added: 'Added 1 song to playlist',
  removed: 'Removed 1 song from playlist',
  full: `Playlist is full (${PLAYLIST_MAX_SONGS} songs).`,
};

@Injectable()
export class PlaylistService {
  readonly saved = inject(BrowserStorage).record(PLAYLIST_STORAGE);
  private readonly playlistsSignal = computed(() => this.saved.value().items);
  private readonly playlistSortSignal = computed(() => this.saved.value().sort);
  private readonly selectedPlaylistIdSignal = signal<string | null>(null);
  private readonly autoAddEnabledSignal = signal(false);
  readonly playlists = this.playlistsSignal;
  readonly playlistSort = this.playlistSortSignal;
  readonly selectedPlaylistId = this.selectedPlaylistIdSignal.asReadonly();
  readonly autoAddEnabled = this.autoAddEnabledSignal.asReadonly();
  readonly sortedPlaylists = computed(() =>
    sortPlaylists(this.playlistsSignal(), this.playlistSortSignal()),
  );
  readonly selectedPlaylist = computed(() => {
    const selectedId = this.selectedPlaylistIdSignal();
    return this.playlistsSignal().find((playlist) => playlist.id === selectedId) ?? null;
  });
  readonly autoAddPlaylist = computed(() =>
    this.autoAddEnabledSignal() ? this.selectedPlaylist() : null,
  );

  setPlaylistSort(sort: unknown): void {
    const nextSort = parsePlaylistSort(sort);
    this.saved.update(current => ({ ...current, sort: nextSort }));
  }

  resetPlaylistSort(): void {
    this.setPlaylistSort(DEFAULT_PLAYLIST_SORT);
  }

  selectPlaylist(id: string | null): void {
    const selectedId = id && this.findPlaylist(id) ? id : null;
    this.selectedPlaylistIdSignal.set(selectedId);
    if (!selectedId) this.cancelAutoAdd();
  }

  ensureSelectedPlaylist(): Playlist | null {
    const selected = this.selectedPlaylist();
    if (selected) return selected;

    const fallback = this.sortedPlaylists()[0] ?? null;
    this.selectPlaylist(fallback?.id ?? null);
    return fallback;
  }

  setAutoAdd(enabled: boolean): void {
    this.autoAddEnabledSignal.set(enabled && !!this.selectedPlaylist());
  }

  startAutoAdd(playlistId: string): void {
    this.selectPlaylist(playlistId);
    this.autoAddEnabledSignal.set(!!this.selectedPlaylist());
  }

  cancelAutoAdd(): void {
    this.autoAddEnabledSignal.set(false);
  }

  createPlaylist(name: string, annSongIds: number[] = []): Playlist | null {
    const normalizedName = this.normalizeName(name);
    if (!normalizedName) return null;

    const playlist: Playlist = {
      id: this.createId(),
      name: normalizedName,
      createdOn: new Date().toISOString(),
      annSongIds: this.dedupeSongIds(annSongIds),
    };
    this.updatePlaylists([...this.playlistsSignal(), playlist]);
    return playlist;
  }

  renamePlaylist(id: string, name: string): boolean {
    const normalizedName = this.normalizeName(name);
    if (!normalizedName) return false;

    return this.updatePlaylist(id, (playlist) => ({ ...playlist, name: normalizedName })) !== null;
  }

  deletePlaylist(id: string): void {
    if (this.selectedPlaylistIdSignal() === id) {
      this.selectPlaylist(null);
    }
    this.updatePlaylists(this.playlistsSignal().filter((playlist) => playlist.id !== id));
  }

  duplicatePlaylist(id: string): Playlist | null {
    const source = this.findPlaylist(id);
    return source
      ? this.createPlaylist(`Copy of ${source.name}`, source.annSongIds)
      : null;
  }

  appendSongs(id: string, annSongIds: number[]): PlaylistAppendResult | null {
    const playlist = this.findPlaylist(id);
    if (!playlist) return null;

    const requestedIds = this.dedupeSongIds(annSongIds, Infinity);
    const existingIds = new Set(playlist.annSongIds);
    const newIds = requestedIds.filter((songId) => !existingIds.has(songId));
    const availableSlots = Math.max(0, PLAYLIST_MAX_SONGS - playlist.annSongIds.length);
    const addedIds = newIds.slice(0, availableSlots);

    if (addedIds.length) {
      this.updatePlaylist(id, (entry) => ({
        ...entry,
        annSongIds: [...entry.annSongIds, ...addedIds],
      }));
    }

    return {
      addedCount: addedIds.length,
      duplicateCount: requestedIds.length - newIds.length,
      skippedForLimitCount: newIds.length - addedIds.length,
    };
  }

  replaceSongs(id: string, annSongIds: number[]): Playlist | null {
    return this.updatePlaylist(id, (playlist) => ({
      ...playlist,
      annSongIds: this.dedupeSongIds(annSongIds),
    }));
  }

  addSong(playlistId: string, annSongId: unknown): PlaylistAddResult {
    const songId = this.toSongId(annSongId);
    if (songId === null) return 'invalid-song';

    const playlist = this.findPlaylist(playlistId);
    if (!playlist) return 'not-found';

    if (playlist.annSongIds.includes(songId)) {
      return 'duplicate';
    }
    if (playlist.annSongIds.length >= PLAYLIST_MAX_SONGS) {
      return 'full';
    }

    this.updatePlaylist(playlistId, (entry) => ({
      ...entry,
      annSongIds: [...entry.annSongIds, songId],
    }));
    return 'added';
  }

  toggleSong(playlistId: string, annSongId: unknown): PlaylistToggleResult {
    const playlist = this.findPlaylist(playlistId);
    if (playlist && this.containsSong(playlist, annSongId)) {
      this.removeSong(playlistId, annSongId);
      return 'removed';
    }
    return this.addSong(playlistId, annSongId);
  }

  removeSong(playlistId: string, annSongId: unknown): boolean {
    const songId = this.toSongId(annSongId);
    if (songId === null) return false;

    const playlist = this.findPlaylist(playlistId);
    if (!playlist?.annSongIds.includes(songId)) return false;

    this.updatePlaylist(playlistId, (entry) => ({
      ...entry,
      annSongIds: entry.annSongIds.filter((id) => id !== songId),
    }));
    return true;
  }

  containsSong(playlist: Playlist, annSongId: unknown): boolean {
    const songId = this.toSongId(annSongId);
    return songId !== null && playlist.annSongIds.includes(songId);
  }

  annSongIdsFromRows(
    songs: readonly { annSongId?: unknown }[],
    limit = PLAYLIST_MAX_SONGS,
  ): number[] {
    return this.dedupeSongIds(songs.map((song) => song?.annSongId), limit);
  }

  extractAnnSongIds(value: unknown): number[] {
    const ids: number[] = [];
    const seenIds = new Set<number>();
    const seenObjects = new Set<object>();
    const addId = (candidate: unknown) => {
      const songId = this.toSongId(candidate);
      if (songId !== null && !seenIds.has(songId) && ids.length < PLAYLIST_MAX_SONGS) {
        seenIds.add(songId);
        ids.push(songId);
      }
    };
    const visit = (candidate: unknown, allowBareIdArray = false): void => {
      if (ids.length >= PLAYLIST_MAX_SONGS || candidate === null || candidate === undefined) return;
      if (Array.isArray(candidate)) {
        if (
          allowBareIdArray
          && candidate.length > 0
          && candidate.every((item) => typeof item === 'number' || typeof item === 'string')
        ) {
          candidate.forEach(addId);
          return;
        }
        candidate.forEach((item) => visit(item));
        return;
      }
      if (typeof candidate !== 'object' || seenObjects.has(candidate)) return;
      seenObjects.add(candidate);
      for (const [key, nestedValue] of Object.entries(candidate as Record<string, unknown>)) {
        const normalizedKey = key.replace(/[^a-z0-9]/gi, '').toLowerCase();
        if (normalizedKey === 'annsongid') addId(nestedValue);
        else if (normalizedKey === 'annsongids' && Array.isArray(nestedValue)) nestedValue.forEach(addId);
        else visit(nestedValue);
      }
    };
    visit(value, true);
    return ids;
  }

  private updatePlaylists(playlists: Playlist[]): void {
    this.saved.update(current => ({ ...current, items: playlists }));
  }

  private findPlaylist(id: string): Playlist | undefined {
    return this.playlistsSignal().find((playlist) => playlist.id === id);
  }

  /** Replace the playlist with the given id; returns the updated playlist or null when missing. */
  private updatePlaylist(id: string, update: (playlist: Playlist) => Playlist): Playlist | null {
    const playlist = this.findPlaylist(id);
    if (!playlist) return null;

    const updated = update(playlist);
    this.updatePlaylists(this.playlistsSignal().map((entry) => (entry.id === id ? updated : entry)));
    return updated;
  }

  private normalizeName(value: unknown): string | null {
    if (typeof value !== 'string') return null;
    const name = value.trim().slice(0, 100);
    return name || null;
  }

  private dedupeSongIds(ids: readonly unknown[], limit = PLAYLIST_MAX_SONGS): number[] {
    const uniqueIds: number[] = [];
    const seenIds = new Set<number>();

    for (const id of ids) {
      if (uniqueIds.length >= limit) break;
      const songId = this.toSongId(id);
      if (songId !== null && !seenIds.has(songId)) {
        seenIds.add(songId);
        uniqueIds.push(songId);
      }
    }

    return uniqueIds;
  }

  private toSongId(value: unknown): number | null {
    return parseNonNegativeInteger(value);
  }

  private createId(): string {
    return typeof crypto?.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }

}
