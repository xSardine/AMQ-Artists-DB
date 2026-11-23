import { DestroyRef, inject, Injectable, signal } from '@angular/core';

type NotificationState = {
  message: string;
  phase: 'visible' | 'exiting';
};

@Injectable()
export class NotificationService {
  private readonly destroyRef = inject(DestroyRef);
  private readonly visibleMs = 2000;
  private readonly fadeMs = 200;
  private visibleTimeout?: ReturnType<typeof setTimeout>;
  private fadeTimeout?: ReturnType<typeof setTimeout>;

  private readonly stateSignal = signal<NotificationState | null>(null);
  readonly state = this.stateSignal.asReadonly();

  constructor() {
    this.destroyRef.onDestroy(() => this.clearTimers());
  }

  show(message: string): void {
    if (this.destroyRef.destroyed) return;
    this.clearTimers();
    this.stateSignal.set({ message, phase: 'visible' });

    this.visibleTimeout = setTimeout(() => {
      this.visibleTimeout = undefined;
      this.stateSignal.set({ message, phase: 'exiting' });
      this.fadeTimeout = setTimeout(() => {
        this.fadeTimeout = undefined;
        this.stateSignal.set(null);
      }, this.fadeMs);
    }, this.visibleMs);
  }

  private clearTimers(): void {
    if (this.visibleTimeout !== undefined) {
      clearTimeout(this.visibleTimeout);
      this.visibleTimeout = undefined;
    }
    if (this.fadeTimeout !== undefined) {
      clearTimeout(this.fadeTimeout);
      this.fadeTimeout = undefined;
    }
  }
}
