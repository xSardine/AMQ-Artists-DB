import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { Subscription, timer } from 'rxjs';
import { getRankedStatus, type RankedStatus } from '../../shared/utils/ranked-schedule';

/** Owns the Search page's ranked-status ticker. */
@Injectable()
export class RankedStatusService {
  private readonly destroyRef = inject(DestroyRef);
  private ticker: Subscription | null = null;
  private readonly statusSignal = signal(getRankedStatus());
  readonly status = this.statusSignal.asReadonly();
  readonly active = computed(() => this.status().active);

  constructor() {
    this.destroyRef.onDestroy(() => this.stop());
    this.start();
  }

  start(): void {
    if (this.destroyRef.destroyed || this.ticker) return;
    this.refresh();
    this.ticker = timer(1000, 1000).subscribe(() => this.refresh());
  }

  stop(): void {
    this.ticker?.unsubscribe();
    this.ticker = null;
  }

  getStatus(date: Date = new Date()): RankedStatus {
    return getRankedStatus(date);
  }

  private refresh(): void {
    const next = getRankedStatus();
    const previous = this.status();
    if (previous.active !== next.active
      || previous.region !== next.region
      || previous.remainingSeconds !== next.remainingSeconds) {
      this.statusSignal.set(next);
    }
  }
}
