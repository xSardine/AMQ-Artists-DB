import { ChangeDetectionStrategy, Component, computed, effect, inject, signal } from '@angular/core';
import { AudioPlaybackService } from '../audio/audio-playback.service';
import { ColumnSettingsComponent } from '../../../shared/controls/column-settings.component';
import { ClipboardService } from '../../../shared/feedback/clipboard.service';
import { downloadJsonFile } from '../../../shared/utils/json-file';
import { RankedStatusService } from '../ranked-status.service';
import { SearchModalService } from '../search-modal.service';
import { NotificationService } from '../../../shared/feedback/notification.service';
import { SearchPreferencesService } from '../settings/search-preferences.service';
import { SongTableStatsComponent } from './song-table-stats.component';
import { collectPersonIds } from './song-credits';
import { hasAnnSongId, hasSongPlaybackSource, SongCredit, Song } from '../songs/song';
import { PLAYLIST_TOGGLE_MESSAGES, PlaylistService } from '../playlist/playlist.service';
import { SearchService } from '../query/search.service';
import { SongWorkspaceStore } from '../songs/song-workspace.store';
import { getColumnCopyValue, getColumnDisplayValue, SongColumnDefinition } from './song-table-columns';
import { SongTableExtensionCellDirective } from './song-table-extension-cell.directive';
import { ANIME_LIST_SITES, SONG_DIST_LINKS } from './song-links';
import { SongTableController } from './song-table.controller';

type ReorderDragState<Item> = {
  dragged: Item;
  over: Item | null;
  insertAfter: boolean;
};

@Component({
  selector: 'app-song-table',
  templateUrl: './song-table.component.html',
  styleUrls: ['./song-table.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(document:keydown.escape)': 'closeTableStats()',
  },
  imports: [SongTableExtensionCellDirective, SongTableStatsComponent, ColumnSettingsComponent],
})
export class SongTableComponent {
  private readonly searches = inject(SearchService);
  readonly workspace = inject(SongWorkspaceStore);
  readonly table = inject(SongTableController);
  readonly audioPlayback = inject(AudioPlaybackService);
  readonly clipboard = inject(ClipboardService);
  private readonly notifications = inject(NotificationService);
  readonly preferences = inject(SearchPreferencesService);
  private readonly rankedStatusService = inject(RankedStatusService);
  private readonly modals = inject(SearchModalService);
  private readonly playlistService = inject(PlaylistService);

  readonly searchErrorMessage = this.searches.searchError;
  readonly rankedActive = this.rankedStatusService.active;

  readonly songTable = this.workspace.songs;
  readonly animeTitleLang = computed(
    () => this.preferences.preferences().animeTitleLanguage,
  );
  readonly currentAudioSong = this.audioPlayback.currentSong;

  readonly tableHeaders = this.table.visibleColumns;
  readonly availableColumns = this.table.availableColumns;
  readonly visibleColumnIds = computed(() => this.tableHeaders().map(column => column.id));
  readonly showColumnSettings = signal(false);
  readonly showTableStats = signal(false);
  private readonly autoAddSongIds = computed(
    () => new Set(this.playlistService.autoAddPlaylist()?.annSongIds ?? []),
  );
  readonly animeListSites = ANIME_LIST_SITES;
  readonly songDistLinks = SONG_DIST_LINKS;

  readonly sortState = this.table.sortState;
  private readonly songDrag = signal<ReorderDragState<Song> | null>(null);

  readonly isSongPlayable = hasSongPlaybackSource;
  readonly hasAnnSongId = hasAnnSongId;

  downloadJson(): void {
    downloadJsonFile(this.workspace.downloadFileName(), this.songTable() ?? []);
  }

  openPlaylistPicker(song: Song): void {
    if (!hasAnnSongId(song)) return;

    const playlist = this.playlistService.ensureSelectedPlaylist();
    if (this.playlistService.autoAddEnabled() && playlist) {
      const result = this.playlistService.toggleSong(playlist.id, song.annSongId);
      const message = PLAYLIST_TOGGLE_MESSAGES[result];
      if (message) this.notifications.show(message);
      return;
    }

    this.modals.open({ type: 'playlist-picker', song });
  }

  isAlreadyInAutoAddPlaylist(song: Song): boolean {
    return this.autoAddSongIds().has(song.annSongId);
  }

  constructor() {
    effect(() => {
      const activeModal = this.modals.active();
      if (activeModal) {
        this.showTableStats.set(false);
        this.showColumnSettings.set(false);
      }
    });
  }

  isCurrentAudioSong(song: Song) {
    return song.annSongId === this.currentAudioSong()?.annSongId;
  }

  private closeSongInfoPopup() {
    this.modals.close('song-info');
  }

  closeTableStats(): void {
    this.showTableStats.set(false);
  }

  getColumnDisplayValue(song: Song, column: SongColumnDefinition) {
    return getColumnDisplayValue(song, column, this.animeTitleLang());
  }

  getColumnCopyValue(song: Song, column: SongColumnDefinition) {
    return getColumnCopyValue(song, column, this.animeTitleLang());
  }

  displaySongInfoPopup(song: Song) {
    const activeModal = this.modals.active();
    if (activeModal?.type === 'song-info' && activeModal.song === song) {
      this.closeSongInfoPopup();
      return;
    }

    this.modals.open({ type: 'song-info', song });
  }

  onRowDragStart(event: DragEvent, song: Song) {
    this.songDrag.set({
      dragged: song,
      over: null,
      insertAfter: false,
    });
    event.stopPropagation();

    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', '');
    }
  }

  onRowDragOver(event: DragEvent, song: Song) {
    const drag = this.songDrag();
    if (!drag || drag.dragged === song) {
      return;
    }

    event.preventDefault();
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    this.songDrag.set({
      ...drag,
      over: song,
      insertAfter: event.clientY > rect.top + rect.height / 2,
    });

    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move';
    }
  }

  onRowDrop(event: DragEvent, targetSong: Song) {
    event.preventDefault();
    event.stopPropagation();

    const drag = this.songDrag();
    if (drag) {
      this.workspace.move(drag.dragged, targetSong, drag.insertAfter);
    }
    this.clearDragState();
  }

  onRowDragEnd() {
    this.clearDragState();
  }

  isDraggingSong(song: Song) {
    return this.songDrag()?.dragged === song;
  }

  isDragOverBefore(song: Song) {
    const drag = this.songDrag();
    return !!drag && drag.over === song && !drag.insertAfter;
  }

  isDragOverAfter(song: Song) {
    const drag = this.songDrag();
    return !!drag && drag.over === song && drag.insertAfter;
  }

  private clearDragState() {
    this.songDrag.set(null);
  }

  searchArtistIds(artists: SongCredit[]): void {
    this.searches.searchArtistIds(collectPersonIds(artists));
  }

  searchComposerIds(composers: SongCredit[]): void {
    this.searches.searchComposerIds(collectPersonIds(composers));
  }

  searchAnnId(id: string | number): void {
    this.searches.searchAnnIds([id]);
  }
}
