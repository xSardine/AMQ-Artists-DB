import { computed, Injectable, signal } from '@angular/core';
import type { Song } from './song';

type SongWorkspaceSort = {
  column: string;
  ascending: boolean;
};

type SongWorkspaceState = {
  songs: readonly Song[] | null;
  sort: SongWorkspaceSort | null;
  downloadFileName: string;
};

/** Owns the application's current editable, ordered collection of songs. */
@Injectable()
export class SongWorkspaceStore {
  private readonly stateSignal = signal<SongWorkspaceState>({
    songs: null,
    sort: null,
    downloadFileName: 'SongList.json',
  });

  readonly state = this.stateSignal.asReadonly();
  readonly songs = computed(() => this.stateSignal().songs);
  readonly sortState = computed(() => this.stateSignal().sort);
  readonly downloadFileName = computed(() => this.stateSignal().downloadFileName);

  /** Replaces results, sort, and download metadata as one state change. */
  replace(
    songs: readonly Song[],
    sort: SongWorkspaceSort | null,
    downloadFileName = 'SongList.json',
  ): void {
    this.stateSignal.set({ songs, sort, downloadFileName });
  }

  sort(
    compare: (left: Song, right: Song) => number,
    sort: SongWorkspaceSort,
  ): boolean {
    const state = this.stateSignal();
    if (!state.songs) return false;

    this.stateSignal.set({
      ...state,
      songs: [...state.songs].sort(compare),
      sort,
    });
    return true;
  }

  shuffle(random: () => number = Math.random): boolean {
    const state = this.stateSignal();
    if (!state.songs || state.songs.length < 2) return false;

    const shuffled = [...state.songs];
    for (let index = shuffled.length - 1; index > 0; index -= 1) {
      const randomIndex = Math.floor(random() * (index + 1));
      [shuffled[index], shuffled[randomIndex]] = [shuffled[randomIndex], shuffled[index]];
    }

    this.stateSignal.set({
      ...state,
      songs: shuffled,
      sort: null,
    });
    return true;
  }

  remove(song: Song): boolean {
    const state = this.stateSignal();
    const index = state.songs?.indexOf(song) ?? -1;
    if (!state.songs || index < 0) return false;

    this.stateSignal.set({
      ...state,
      songs: [
        ...state.songs.slice(0, index),
        ...state.songs.slice(index + 1),
      ],
    });
    return true;
  }

  move(movedSong: Song, targetSong: Song, insertAfter: boolean): boolean {
    const state = this.stateSignal();
    if (!state.songs || movedSong === targetSong) return false;

    const sourceIndex = state.songs.indexOf(movedSong);
    if (sourceIndex < 0 || !state.songs.includes(targetSong)) return false;

    const reordered = [...state.songs];
    reordered.splice(sourceIndex, 1);
    let targetIndex = reordered.indexOf(targetSong);
    if (insertAfter) targetIndex += 1;
    reordered.splice(targetIndex, 0, movedSong);

    this.stateSignal.set({
      ...state,
      songs: reordered,
      sort: null,
    });
    return true;
  }

  clearSort(): void {
    const state = this.stateSignal();
    if (!state.sort) return;

    this.stateSignal.set({
      ...state,
      sort: null,
    });
  }
}
