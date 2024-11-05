import { DOCUMENT } from '@angular/common';
import { Inject, Injectable } from '@angular/core';
import { THEMES } from '../config/theme.config';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  constructor(@Inject(DOCUMENT) private document: Document) {}

  current_theme: string = 'default';
  toggleTheme() {
    if (this.current_theme == 'default') {
      this.current_theme = 'dark';
    } else {
      this.current_theme = 'default';
    }
    // @ts-ignore
    const theme = THEMES[this.current_theme];
    Object.keys(theme).forEach((key) => {
      this.document.documentElement.style.setProperty(`--${key}`, theme[key]);
    });
  }
}
