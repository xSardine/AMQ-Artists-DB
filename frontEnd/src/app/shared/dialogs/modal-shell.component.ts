import { afterNextRender, ChangeDetectionStrategy, Component, ElementRef, input, OnDestroy, output, viewChild } from '@angular/core';

type ModalSize = 'compact' | 'medium' | 'wide';

let nextModalId = 0;

@Component({
  selector: 'app-modal-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './modal-shell.component.html',
  styleUrls: ['./modal-shell.component.css'],
})
export class ModalShellComponent implements OnDestroy {
  private readonly generatedId = `app-modal-${++nextModalId}`;
  private readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');
  private readonly closeButton = viewChild.required<ElementRef<HTMLButtonElement>>('closeButton');
  private readonly returnFocus = document.activeElement as HTMLElement | null;
  private focusRestored = false;

  readonly modalTitle = input<string>();
  readonly titleId = input(`${this.generatedId}-title`);
  readonly closeLabel = input('Close dialog');
  readonly dialogId = input(this.generatedId);
  readonly closeButtonId = input(`${this.generatedId}-close`);
  readonly size = input<ModalSize>('medium');
  readonly fillHeight = input(false);
  readonly closeDisabled = input(false);
  readonly closed = output<void>();

  constructor() {
    afterNextRender(() => {
      const dialog = this.dialog().nativeElement;
      dialog.showModal();
      const initialFocus = dialog.querySelector<HTMLElement>('[data-modal-initial-focus]');
      (initialFocus ?? this.closeButton().nativeElement).focus({ preventScroll: true });
    });
  }

  close(): void {
    if (this.closeDisabled()) return;
    const dialog = this.dialog().nativeElement;
    if (dialog.open) {
      dialog.close();
    }
  }

  onClose(): void {
    this.restoreFocus();
    this.closed.emit();
  }

  onCancel(event: Event): void {
    if (this.closeDisabled()) event.preventDefault();
  }

  ngOnDestroy(): void {
    // Feature actions can remove a modal by changing application state instead
    // of calling dialog.close(), so destruction must preserve focus as well.
    this.restoreFocus();
  }

  onDialogClick(event: MouseEvent): void {
    if (event.target !== this.dialog().nativeElement) return;

    const rect = this.dialog().nativeElement.getBoundingClientRect();
    const outsideDialog = event.clientX < rect.left
      || event.clientX > rect.right
      || event.clientY < rect.top
      || event.clientY > rect.bottom;
    if (outsideDialog) this.close();
  }

  private restoreFocus(): void {
    if (this.focusRestored) return;
    this.focusRestored = true;
    if (this.returnFocus?.isConnected) {
      this.returnFocus.focus({ preventScroll: true });
    }
  }
}
