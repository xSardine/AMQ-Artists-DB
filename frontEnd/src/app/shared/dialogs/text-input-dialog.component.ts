import { ChangeDetectionStrategy, Component, input, model, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ModalShellComponent } from './modal-shell.component';

@Component({
  selector: 'app-text-input-dialog',
  imports: [FormsModule, ModalShellComponent],
  templateUrl: './text-input-dialog.component.html',
  styleUrl: './action-dialog.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextInputDialogComponent {
  readonly title = input.required<string>();
  readonly label = input('Name');
  readonly value = model('');
  readonly maxLength = input(100);
  readonly busy = input(false);
  readonly error = input('');
  readonly idPrefix = input('text-input');
  readonly confirmLabel = input('Save');
  readonly submitted = output<string>();
  readonly cancelled = output<void>();
}
