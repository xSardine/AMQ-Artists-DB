import { Injectable, signal, untracked } from '@angular/core';
import { Song } from './songs/song';

type SearchModal =
  | { type: 'settings' }
  | { type: 'playlists' }
  | { type: 'song-info'; song: Song }
  | { type: 'playlist-picker'; song: Song };

type SearchModalType = SearchModal['type'];

@Injectable()
export class SearchModalService {
  private readonly activeModal = signal<SearchModal | null>(null);
  readonly active = this.activeModal.asReadonly();

  open(modal: SearchModal): void {
    this.activeModal.set(modal);
  }

  close(type?: SearchModalType): void {
    // Closing is a command, so callers should not become reactive consumers of
    // the active modal just because they conditionally close one from an effect.
    untracked(() => {
      if (type && this.active()?.type !== type) return;
      this.activeModal.set(null);
    });
  }
}
