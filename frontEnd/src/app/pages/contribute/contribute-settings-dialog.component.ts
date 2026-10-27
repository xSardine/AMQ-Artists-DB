import { ChangeDetectionStrategy, Component, output } from '@angular/core';
import { ModalShellComponent } from '../../shared/dialogs/modal-shell.component';
import { ThemeSelectorComponent } from '../../shared/controls/theme-selector.component';

@Component({
  selector: 'app-contribute-settings-dialog',
  imports: [ModalShellComponent, ThemeSelectorComponent],
  templateUrl: './contribute-settings-dialog.component.html',
  host: { style: 'display: contents' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContributeSettingsDialogComponent {
  readonly closed = output<void>();
}
