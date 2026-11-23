import { ChangeDetectionStrategy, Component, output } from '@angular/core';
import { ModalShellComponent } from '../../shared/dialogs/modal-shell.component';
import { ThemeSelectorComponent } from '../../shared/controls/theme-selector.component';

@Component({
  selector: 'app-stats-settings-dialog',
  imports: [ModalShellComponent, ThemeSelectorComponent],
  templateUrl: './stats-settings-dialog.component.html',
  host: { style: 'display: contents' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatsSettingsDialogComponent {
  readonly closed = output<void>();
}
