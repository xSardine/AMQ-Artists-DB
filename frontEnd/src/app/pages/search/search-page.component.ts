import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ToolbarComponent } from '../../shared/layout/toolbar.component';
import { SearchToolbarControlsComponent } from './search-toolbar-controls.component';
import { SearchModalService } from './search-modal.service';
import { AudioPlayerComponent } from './audio/audio-player.component';
import { UserscriptBridgeService } from './extensions/userscript-bridge.service';
import { AudioPlaybackService } from './audio/audio-playback.service';
import { SearchModalOutletComponent } from './search-modal-outlet.component';
import { SearchBarComponent } from './query/search-bar.component';
import { SearchService } from './query/search.service';
import { ToastOutletComponent } from '../../shared/feedback/toast-outlet.component';
import { SongTableComponent } from './song-table/song-table.component';
import { RankedStatusService } from './ranked-status.service';
import { SearchBackupService } from './settings/search-backup.service';
import { SearchPreferencesService } from './settings/search-preferences.service';
import { SearchSettingsTabRegistryService } from './settings/search-settings-tab-registry.service';
import { SongTableController } from './song-table/song-table.controller';
import { SongWorkspaceStore } from './songs/song-workspace.store';
import { PlaylistService } from './playlist/playlist.service';
import { ClipboardService } from '../../shared/feedback/clipboard.service';
import { NotificationService } from '../../shared/feedback/notification.service';

@Component({
  selector: 'app-search-page',
  templateUrl: './search-page.component.html',
  styleUrl: './search-page.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ToolbarComponent,
    SearchToolbarControlsComponent,
    SearchModalOutletComponent,
    AudioPlayerComponent,
    SearchBarComponent,
    SongTableComponent,
    ToastOutletComponent,
  ],
  providers: [
    SearchService,
    SongWorkspaceStore,
    SongTableController,
    AudioPlaybackService,
    PlaylistService,
    SearchModalService,
    SearchPreferencesService,
    SearchBackupService,
    SearchSettingsTabRegistryService,
    RankedStatusService,
    UserscriptBridgeService,
    NotificationService,
    ClipboardService,
  ],
})
export class SearchPageComponent {
  private readonly searches = inject(SearchService);
  readonly modals = inject(SearchModalService);

  constructor() {
    inject(UserscriptBridgeService);
    this.searches.startInitialSearch();
  }
}
