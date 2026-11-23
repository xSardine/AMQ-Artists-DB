import { ChangeDetectionStrategy, Component, inject, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ModalShellComponent } from '../../shared/dialogs/modal-shell.component';
import { ThemeSelectorComponent } from '../../shared/controls/theme-selector.component';
import { LogState } from './log-state';

@Component({
  selector: 'app-log-settings-dialog',
  imports: [FormsModule, ModalShellComponent, ThemeSelectorComponent],
  templateUrl: './log-settings-dialog.component.html',
  styleUrl: './log-settings-dialog.component.css',
  host: { style: 'display: contents' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogSettingsDialogComponent {
  readonly state = inject(LogState);
  readonly closed = output<void>();

  updateEventLimit(input: HTMLInputElement): void {
    const value = input.valueAsNumber;
    if (input.validity.valid && Number.isInteger(value)) {
      this.state.setEventLimit(value);
    }
    input.value = String(this.state.eventLimit());
  }

  async logout(): Promise<void> {
    await this.state.logout();
    if (!this.state.authenticated()) this.closed.emit();
  }
}
