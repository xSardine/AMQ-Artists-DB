import { afterNextRender, ChangeDetectionStrategy, Component, computed, CUSTOM_ELEMENTS_SCHEMA, effect, ElementRef, inject, OnDestroy, signal, viewChild } from '@angular/core';
import { LocalMediaStorage, MediaPlayer } from 'vidstack';
import { getSongPlaybackSource } from '../songs/song';
import { SearchPreferencesService } from '../settings/search-preferences.service';
import { ThemeService } from '../../../core/theme.service';
import { AudioPlaybackCommand, AudioPlaybackService } from './audio-playback.service';
import 'vidstack/player';
import 'vidstack/player/layouts/default';
import 'vidstack/player/ui';

type ConfigurableMediaPlayer = MediaPlayer & {
  crossOrigin: boolean;
  keyTarget: string;
  src: string;
};

class SessionMediaStorage extends LocalMediaStorage {
  override async getTime(): Promise<number | null> { return null; }
  override async setTime(_time: number, _ended: boolean): Promise<void> {}
}

@Component({
  selector: 'app-audio-player',
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './audio-player.component.html',
  styleUrls: ['./audio-player.component.css'],
})
export class AudioPlayerComponent implements OnDestroy {
  readonly playback = inject(AudioPlaybackService);
  readonly playerVisible = signal(false);
  readonly storage = new SessionMediaStorage();
  readonly theme = inject(ThemeService);
  private readonly preferences = inject(SearchPreferencesService);
  private readonly playerRef = viewChild<ElementRef<MediaPlayer>>('player');
  private requestAbort?: AbortController;
  private player?: MediaPlayer;
  private loadedAnnSongId: number | null = null;
  private destroyed = false;

  constructor() {
    afterNextRender(() => void this.initializePlayer());
    effect(() => {
      const command = this.playback.command();
      void this.execute(command);
    });
  }

  readonly playerTitle = computed(() => {
    const song = this.playback.currentSong();
    return song ? `${song.songName} by ${song.songArtist}` : '';
  });

  ngOnDestroy(): void {
    this.destroyed = true;
    this.requestAbort?.abort();
    this.player?.pause();
    this.playback.stop();
    this.player?.removeEventListener('play', this.onPlay);
    this.player?.removeEventListener('pause', this.onPause);
    this.player?.removeEventListener('ended', this.onEnded);
  }

  private async initializePlayer(): Promise<void> {
    await customElements.whenDefined('media-player');
    if (this.destroyed) return;
    const player = this.playerRef()?.nativeElement;
    if (!player) return;
    this.player = player;
    const configurablePlayer = player as ConfigurableMediaPlayer;
    configurablePlayer.crossOrigin = true;
    configurablePlayer.keyTarget = 'document';
    player.addEventListener('play', this.onPlay);
    player.addEventListener('pause', this.onPause);
    player.addEventListener('ended', this.onEnded);
    player.startLoading?.();
    void this.execute(this.playback.command());
  }

  private async execute(command: AudioPlaybackCommand): Promise<void> {
    const player = this.player;
    if (!player) return;
    this.requestAbort?.abort();
    this.requestAbort = new AbortController();
    const signal = this.requestAbort.signal;

    if (command.type === 'stop' || command.type === 'pause') {
      player.pause();
      return;
    }

    try {
      const source = getSongPlaybackSource(command.song);
      if (!source) {
        throw new Error('Song has no playable media source');
      }

      this.playerVisible.set(true);

      if (this.loadedAnnSongId === command.song.annSongId) {
        if (command.type === 'restart') player.currentTime = 0;
        if (command.type === 'seek') {
          player.currentTime = command.time;
          return;
        }
        await player.play();
        return;
      }

      const ready = this.waitForCanPlay(player, signal);
      this.loadedAnnSongId = null;
      (player as ConfigurableMediaPlayer).src = this.preferences.getDistUrl(source);
      player.title = `${command.song.songName} by ${command.song.songArtist}`;
      await ready;
      if (signal.aborted) return;
      this.loadedAnnSongId = command.song.annSongId;
      if (command.type === 'seek') player.currentTime = command.time;
      if (command.type === 'seek' && this.playback.state().status === 'paused') return;
      await player.play();
    } catch (error) {
      if (!signal.aborted) {
        console.error('Error playing song:', error);
        this.playback.markFailed(command.id, error);
      }
    }
  }

  private waitForCanPlay(player: MediaPlayer, signal: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
      let timeout: ReturnType<typeof setTimeout>;
      const onCanPlay = () => finish(resolve);
      const onError = (event: Event) => finish(() => reject(event));
      const onAbort = () => finish(() => reject(new DOMException('Aborted', 'AbortError')));
      const finish = (complete: () => void) => {
        clearTimeout(timeout);
        player.removeEventListener('can-play', onCanPlay);
        player.removeEventListener('error', onError);
        signal.removeEventListener('abort', onAbort);
        complete();
      };
      timeout = setTimeout(() => finish(() => reject(new Error('Audio loading timed out'))), 15_000);
      player.addEventListener('can-play', onCanPlay);
      player.addEventListener('error', onError);
      signal.addEventListener('abort', onAbort, { once: true });
    });
  }

  private readonly onEnded = () => {
    const current = this.playback.currentSong();
    const player = this.player;
    if (!current || !player) return;
    const mode = this.preferences.preferences().radioMode;
    if (mode === 'repeat') {
      this.playback.restart();
      return;
    }
    if (mode !== 'loop-all') {
      this.playback.stop();
      return;
    }
    if (this.playback.next()) return;
    if (this.playback.currentSongIsInResults()) {
      // Loop All should still loop when the current row is the table's only
      // playable song. If a new search removed it, stop instead.
      this.playback.restart();
      return;
    }
    this.playback.stop();
  };

  private readonly onPlay = () => {
    const command = this.playback.command();
    if (command.type !== 'stop' && this.loadedAnnSongId === command.song.annSongId) {
      this.playback.markPlaying(command.id, command.song);
    }
  };

  private readonly onPause = () => {
    const command = this.playback.command();
    if (command.type !== 'stop' && this.loadedAnnSongId === command.song.annSongId) {
      this.playback.markPaused(command.id, command.song);
    }
  };
}
