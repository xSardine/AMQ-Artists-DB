import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { ThemeService } from '../../core/theme.service';
import { THEME_OPTIONS } from '../../core/theme';
import { SegmentedRadioComponent } from './segmented-radio.component';

let nextThemeSelectorId = 0;

@Component({
  selector: 'app-theme-selector',
  imports: [SegmentedRadioComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-segmented-radio [options]="options" [value]="theme.theme()" [name]="controlId()"
      label="Theme" (valueChange)="theme.select($event)" />
  `,
  styleUrl: './theme-selector.component.css',
})
export class ThemeSelectorComponent {
  readonly theme = inject(ThemeService);
  readonly options = THEME_OPTIONS;
  readonly controlId = input(`theme-${++nextThemeSelectorId}`);
}
