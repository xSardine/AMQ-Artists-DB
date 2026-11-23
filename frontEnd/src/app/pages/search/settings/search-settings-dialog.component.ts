import { ChangeDetectionStrategy, Component, DestroyRef, effect, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ConfirmDialogComponent } from '../../../shared/dialogs/confirm-dialog.component';
import { ThemeSelectorComponent } from '../../../shared/controls/theme-selector.component';
import { InfoPopoverComponent } from '../../../shared/controls/info-popover.component';
import { ClipboardPopupOutletComponent } from '../../../shared/feedback/clipboard-popup-outlet.component';
import {
  ANIME_TITLE_LANGUAGE_OPTIONS,
  DIST_SERVER_OPTIONS,
  RADIO_MODE_OPTIONS,
} from './search-preferences';
import { SearchBackupService, SearchDataScope } from './search-backup.service';
import { NotificationService } from '../../../shared/feedback/notification.service';
import { SearchPreferencesService } from './search-preferences.service';
import { ModalShellComponent } from '../../../shared/dialogs/modal-shell.component';
import { SegmentedRadioComponent } from '../../../shared/controls/segmented-radio.component';
import { SettingsTabPanelDirective } from './settings-tab-panel.directive';
import { SearchSettingsTabRegistryService } from './search-settings-tab-registry.service';

interface DataConfirmation {
  title: string;
  message: string;
  confirmLabel: string;
  successMessage: string;
  run: () => Promise<void>;
}

@Component({
  selector: 'app-search-settings-dialog',
  imports: [
    ClipboardPopupOutletComponent,
    ConfirmDialogComponent,
    FormsModule,
    ModalShellComponent,
    SegmentedRadioComponent,
    SettingsTabPanelDirective,
    ThemeSelectorComponent,
    InfoPopoverComponent,
  ],
  templateUrl: './search-settings-dialog.component.html',
  styleUrl: './search-settings-dialog.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SearchSettingsDialogComponent {
  readonly closed = output<void>();
  readonly settingsTabRegistry = inject(SearchSettingsTabRegistryService);
  readonly activeTab = signal<string>('settings');
  readonly searchPreferences = inject(SearchPreferencesService);
  private readonly backups = inject(SearchBackupService);
  readonly dataBusy = signal(false);
  readonly dataConfirmation = signal<DataConfirmation | null>(null);
  readonly dataError = signal('');
  private readonly notifications = inject(NotificationService);
  private readonly destroyRef = inject(DestroyRef);

  readonly preferences = this.searchPreferences.preferences;
  readonly animeTitleLanguages = ANIME_TITLE_LANGUAGE_OPTIONS.map(option => ({
    id: option.id,
    label: option.id === 'EN' ? 'English' : 'Japanese',
  }));
  readonly distServers = DIST_SERVER_OPTIONS;
  readonly radioModes = RADIO_MODE_OPTIONS;

  constructor() {
    effect(() => {
      if (!this.settingsTabRegistry.tabs().some((tab) => tab.id === this.activeTab())) {
        this.activeTab.set('settings');
      }
    });
  }

  setTab(tab: string): void {
    if (this.settingsTabRegistry.tabs().some((candidate) => candidate.id === tab)) {
      this.activeTab.set(tab);
    }
  }

  onTabKeydown(event: KeyboardEvent): void {
    const tabs = this.settingsTabRegistry.tabs();
    const current = tabs.findIndex((tab) => tab.id === this.activeTab());
    let next = current;
    if (event.key === 'ArrowRight') next = (current + 1) % tabs.length;
    else if (event.key === 'ArrowLeft') next = (current - 1 + tabs.length) % tabs.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = tabs.length - 1;
    else return;
    event.preventDefault();
    this.setTab(tabs[next].id);
    document.getElementById(`settings-tab-${tabs[next].id}`)?.focus();
  }

  exportSearchData(): void {
    this.backups.export();
    this.notifications.show('Search data exported');
  }

  onSearchDataImport(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (file) void this.importSearchData(file);
  }

  requestReset(scope: SearchDataScope): void {
    if (this.dataBusy() || this.dataConfirmation()) return;
    const descriptions = {
      preferences: { message: 'Reset search preferences in this browser?' },
      table: { message: 'Reset table columns in this browser?' },
      playlists: { message: 'Delete all playlists in this browser?' },
    };
    this.dataError.set('');
    this.dataConfirmation.set({
      title: "Confirm",
      confirmLabel: "Yes",
      message: descriptions[scope].message,
      successMessage: 'Saved data reset',
      run: () => this.backups.reset(scope),
    });
  }

  cancelDataAction(): void {
    if (this.dataBusy()) return;
    this.dataConfirmation.set(null);
    this.dataError.set('');
  }

  async confirmDataAction(): Promise<void> {
    const action = this.dataConfirmation();
    if (this.dataBusy() || !action) return;
    this.dataBusy.set(true);
    this.dataError.set('');
    try {
      await action.run();
      if (this.destroyRef.destroyed) return;
      this.dataConfirmation.set(null);
      this.notifications.show(action.successMessage);
    } catch (error) {
      if (!this.destroyRef.destroyed) {
        this.dataError.set(error instanceof Error ? error.message : 'Could not update saved data.');
      }
    } finally {
      if (!this.destroyRef.destroyed) this.dataBusy.set(false);
    }
  }

  private async importSearchData(file: File): Promise<void> {
    if (this.dataBusy() || this.dataConfirmation()) return;
    this.dataBusy.set(true);
    try {
      const backup = await this.backups.read(file);
      if (this.destroyRef.destroyed) return;
      this.dataError.set('');
      this.dataConfirmation.set({
        title: 'Confirm',
        message: 'Replace search settings, table settings, and playlists with this backup?',
        confirmLabel: 'Import',
        successMessage: 'Search data imported',
        run: () => this.backups.import(backup),
      });
    } catch (error) {
      if (!this.destroyRef.destroyed) {
        this.notifications.show(error instanceof Error ? error.message : 'Could not read that backup');
      }
    } finally {
      if (!this.destroyRef.destroyed) this.dataBusy.set(false);
    }
  }
}
