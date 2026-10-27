import { computed, inject, Injectable, signal } from '@angular/core';
import { hasSongPlaybackSource, Song } from '../songs/song';
import { SongWorkspaceStore } from '../songs/song-workspace.store';

type AudioPlaybackState =
  | { status: 'idle'; song: null; error: null }
  | { status: 'loading'; song: Song; error: null }
  | { status: 'playing'; song: Song; error: null }
  | { status: 'paused'; song: Song; error: null }
  | { status: 'error'; song: null; error: string };

export type AudioPlaybackCommand =
  | { id: number; type: 'play'; song: Song }
  | { id: number; type: 'restart'; song: Song }
  | { id: number; type: 'seek'; song: Song; time: number }
  | { id: number; type: 'pause'; song: Song }
  | { id: number; type: 'stop' };

@Injectable()
export class AudioPlaybackService {
  private readonly workspace = inject(SongWorkspaceStore);
  private nextCommandId = 0;
  private readonly commandSignal = signal<AudioPlaybackCommand>({ id: 0, type: 'stop' });
  private readonly stateSignal = signal<AudioPlaybackState>({ status: 'idle', song: null, error: null });

  readonly command = this.commandSignal.asReadonly();
  readonly state = this.stateSignal.asReadonly();
  readonly currentSong = computed(() => {
    const state = this.stateSignal();
    return state.status === 'loading' || state.status === 'playing' || state.status === 'paused'
      ? state.song
      : null;
  });

  play(song: Song): void {
    const state = this.stateSignal();
    if (
      (state.status === 'loading' || state.status === 'playing')
      && state.song.annSongId === song.annSongId
    ) return;

    const command = { id: ++this.nextCommandId, type: 'play' as const, song };
    this.stateSignal.set({ status: 'loading', song, error: null });
    this.commandSignal.set(command);
  }

  pause(): boolean {
    const state = this.stateSignal();
    if (state.status !== 'loading' && state.status !== 'playing') return false;

    this.stateSignal.set({ status: 'paused', song: state.song, error: null });
    this.commandSignal.set({
      id: ++this.nextCommandId,
      type: 'pause',
      song: state.song,
    });
    return true;
  }

  next(): boolean {
    return this.playAdjacentSong(1);
  }

  previous(): boolean {
    return this.playAdjacentSong(-1);
  }

  restart(): boolean {
    const song = this.currentSong();
    if (!song) return false;

    // Restart is its own command so ended media is reset by the player command
    // handler instead of racing the media element's final pause/ended events.
    this.stateSignal.set({ status: 'loading', song, error: null });
    this.commandSignal.set({
      id: ++this.nextCommandId,
      type: 'restart',
      song,
    });
    return true;
  }

  seek(time: number): boolean {
    if (!Number.isFinite(time) || time < 0) {
      throw new RangeError('Seek time must be a finite, non-negative number');
    }

    const song = this.currentSong();
    if (!song) return false;

    this.commandSignal.set({
      id: ++this.nextCommandId,
      type: 'seek',
      song,
      time,
    });
    return true;
  }

  currentSongIsInResults(): boolean {
    const current = this.currentSong();
    return !!current && (this.workspace.songs() ?? [])
      .some((song) => song.annSongId === current.annSongId);
  }

  stop(): void {
    this.commandSignal.set({ id: ++this.nextCommandId, type: 'stop' });
    this.stateSignal.set({ status: 'idle', song: null, error: null });
  }

  markPlaying(commandId: number, song: Song): void {
    if (this.commandSignal().id === commandId) {
      this.stateSignal.set({ status: 'playing', song, error: null });
    }
  }

  markPaused(commandId: number, song: Song): void {
    if (this.commandSignal().id !== commandId) return;
    const state = this.stateSignal();
    if (
      (state.status === 'playing' || state.status === 'paused')
      && state.song.annSongId === song.annSongId
    ) {
      this.stateSignal.set({ status: 'paused', song, error: null });
    }
  }

  markFailed(commandId: number, error: unknown): void {
    if (this.commandSignal().id === commandId) {
      const message = error instanceof Error ? error.message : 'Could not play this song';
      this.stateSignal.set({ status: 'error', song: null, error: message });
    }
  }

  private playAdjacentSong(direction: 1 | -1): boolean {
    const current = this.currentSong();
    if (!current) return false;

    const songs = this.workspace.songs() ?? [];
    const currentAnnSongId = current.annSongId;
    const currentIndex = songs.findIndex((song) => song.annSongId === currentAnnSongId);
    if (currentIndex < 0) return false;

    // Do not wrap back to the current song: play() deliberately ignores an
    // already-playing song, so reporting that as a successful move would leave
    // ended media stalled and make manual Next/Previous report a false success.
    for (let offset = 1; offset < songs.length; offset += 1) {
      const index = (currentIndex + direction * offset + songs.length) % songs.length;
      const candidate = songs[index];
      if (
        candidate.annSongId === currentAnnSongId
        || !hasSongPlaybackSource(candidate)
      ) continue;

      this.play(candidate);
      return true;
    }
    return false;
  }
}
