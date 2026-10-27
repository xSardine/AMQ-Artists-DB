import { ChangeDetectionStrategy, Component, inject, output } from '@angular/core';
import { ModalShellComponent } from '../../shared/dialogs/modal-shell.component';
import { ThemeSelectorComponent } from '../../shared/controls/theme-selector.component';
import { ReviewState } from './review-state';

@Component({
  selector: 'app-review-settings-dialog',
  imports: [ModalShellComponent, ThemeSelectorComponent],
  templateUrl: './review-settings-dialog.component.html',
  host: { style: 'display: contents' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReviewSettingsDialogComponent {
  readonly state = inject(ReviewState);
  readonly closed = output<void>();

  async logout(): Promise<void> {
    await this.state.logout();
    if (!this.state.authenticated()) this.closed.emit();
  }
}
