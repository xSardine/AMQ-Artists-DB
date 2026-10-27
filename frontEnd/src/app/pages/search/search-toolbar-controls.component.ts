import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { SearchModalService } from './search-modal.service';
import type { AnimeTitleLanguage } from './settings/search-preferences';
import { SearchPreferencesService } from './settings/search-preferences.service';

@Component({
  selector: 'app-search-toolbar-controls',
  templateUrl: './search-toolbar-controls.component.html',
  styleUrl: './search-toolbar-controls.component.css',
  host: { style: 'display: contents' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SearchToolbarControlsComponent {
  private readonly searchPreferences = inject(SearchPreferencesService);
  readonly modals = inject(SearchModalService);
  readonly preferences = this.searchPreferences.preferences;
  readonly animeTitleLang = computed(() => this.preferences().animeTitleLanguage);

  toggleAnimeLang(): void {
    const animeTitleLanguage: AnimeTitleLanguage =
      this.animeTitleLang() === 'JP' ? 'EN' : 'JP';
    this.searchPreferences.updatePreferences({ animeTitleLanguage });
  }
}
