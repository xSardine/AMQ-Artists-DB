import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { NotificationService } from './notification.service';

type ClipboardPopup = {
  left: string;
  top: string;
};

@Injectable()
export class ClipboardService {
  private readonly notifications = inject(NotificationService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly popupVisibleMs = 500;
  private popupTimeout?: ReturnType<typeof setTimeout>;

  private readonly popupSignal = signal<ClipboardPopup | null>(null);
  readonly popup = this.popupSignal.asReadonly();

  constructor() {
    this.destroyRef.onDestroy(() => this.clearPopupSchedule());
  }

  copy(event: MouseEvent, text: unknown): void {
    if (this.destroyRef.destroyed) return;
    this.clearPopupSchedule();
    this.popupSignal.set({
      left: `${event.clientX + 10}px`,
      top: `${event.clientY - 20}px`,
    });

    // Show success feedback immediately; report a later Clipboard API failure.
    const copyPromise = navigator.clipboard?.writeText(String(text ?? ''));
    if (copyPromise) {
      copyPromise.catch(() => this.notifications.show('Clipboard copy failed.'));
    } else {
      this.notifications.show('Clipboard copy failed.');
    }

    this.popupTimeout = setTimeout(() => {
      this.popupTimeout = undefined;
      this.popupSignal.set(null);
    }, this.popupVisibleMs);
  }

  private clearPopupSchedule(): void {
    if (this.popupTimeout === undefined) return;

    clearTimeout(this.popupTimeout);
    this.popupTimeout = undefined;
  }
}
