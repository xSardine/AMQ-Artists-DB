import { inject, Injectable } from '@angular/core';
import {
  getDistServerOption,
  normalizeSearchPreferences,
  SEARCH_SETTINGS,
  type SearchPreferences,
} from './search-preferences';
import { BrowserStorage } from '../../../core/browser-storage.service';

@Injectable()
export class SearchPreferencesService {
  readonly saved = inject(BrowserStorage).record(SEARCH_SETTINGS);
  readonly preferences = this.saved.value;

  updatePreferences(preferences: Partial<SearchPreferences>): void {
    this.saved.update(current => normalizeSearchPreferences({ ...current, ...preferences }));
  }

  resetPreferences(): void {
    this.saved.set(SEARCH_SETTINGS.defaults());
  }

  getDistUrl(filename: string | null | undefined): string {
    if (!filename) return '';

    const server = getDistServerOption(this.preferences().distServer);
    return `${server.baseUrl}${filename}`;
  }
}
