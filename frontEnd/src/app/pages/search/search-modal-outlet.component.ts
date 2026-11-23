import { ChangeDetectionStrategy, Component, computed, effect, inject } from '@angular/core';
import { PlaylistDialogComponent } from './playlist/playlist-dialog.component';
import { ClipboardPopupOutletComponent } from '../../shared/feedback/clipboard-popup-outlet.component';
import { SongWorkspaceStore } from './songs/song-workspace.store';
import { SongInfoModalComponent } from './song-table/song-info-modal.component';
import { SongPlaylistPickerComponent } from './playlist/song-playlist-picker.component';
import { SearchModalService } from './search-modal.service';
import { SearchSettingsDialogComponent } from './settings/search-settings-dialog.component';

@Component({
  selector: 'app-search-modal-outlet',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ClipboardPopupOutletComponent,
    PlaylistDialogComponent,
    SongInfoModalComponent,
    SongPlaylistPickerComponent,
    SearchSettingsDialogComponent,
  ],
  templateUrl: './search-modal-outlet.component.html',
})
export class SearchModalOutletComponent {
  readonly modals = inject(SearchModalService);
  private readonly workspace = inject(SongWorkspaceStore);

  readonly activeModal = this.modals.active;
  readonly activeSong = computed(() => {
    const modal = this.activeModal();
    if (modal?.type !== 'song-info' && modal?.type !== 'playlist-picker') {
      return null;
    }
    return this.workspace.songs()?.includes(modal.song) ? modal.song : null;
  });

  constructor() {
    effect(() => {
      const modal = this.activeModal();
      if (
        (modal?.type === 'song-info' || modal?.type === 'playlist-picker')
        && !this.activeSong()
      ) {
        this.modals.close(modal.type);
      }
    });
  }
}
