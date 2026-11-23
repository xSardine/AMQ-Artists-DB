import { DOCUMENT, effect, inject, Injectable } from '@angular/core';
import { isThemeId, type ThemeId } from './theme';
import { BrowserStorage, StorageDefinition } from './browser-storage.service';

const THEME_STORAGE: StorageDefinition<ThemeId> = {
  key: 'anisongdb-theme',
  defaults: () => 'classic',
  rawString: true,
  parse(value) {
    if (!isThemeId(value)) throw new Error('Invalid theme.');
    return value;
  },
};

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly saved = inject(BrowserStorage).record(THEME_STORAGE);
  readonly theme = this.saved.value;

  constructor() {
    this.apply(this.theme());
    effect(() => this.apply(this.theme()));
  }

  select(value: string): void {
    if (isThemeId(value)) this.saved.set(value);
  }

  private apply(value: ThemeId): void {
    this.document.documentElement.dataset['theme'] = value;
  }
}
