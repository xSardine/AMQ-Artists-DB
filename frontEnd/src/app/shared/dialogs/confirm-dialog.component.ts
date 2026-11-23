import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { ModalShellComponent } from './modal-shell.component';

@Component({
  selector: 'app-confirm-dialog',
  imports: [ModalShellComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './confirm-dialog.component.html',
  styleUrl: './action-dialog.css',
})
export class ConfirmDialogComponent {
  readonly open = input(false);
  readonly busy = input(false);
  readonly title = input('Confirm action');
  readonly message = input('');
  readonly error = input('');
  readonly idPrefix = input('confirm');
  readonly confirmLabel = input('Confirm');
  readonly busyLabel = input('Saving…');
  readonly destructive = input(false);
  readonly confirmed = output<void>();
  readonly cancelled = output<void>();
}
