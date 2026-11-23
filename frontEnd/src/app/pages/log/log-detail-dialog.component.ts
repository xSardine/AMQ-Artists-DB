import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  ElementRef,
  inject,
  input,
  model,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { ModalShellComponent } from '../../shared/dialogs/modal-shell.component';
import { LogIpComponent } from './log-ip.component';
import { createLogTimeFormatter, describeLogErrors, describeLogEvent, finiteNumber } from './log-presenter';
import { LogEvent, LogTimeSettings } from './log-types';

@Component({
  selector: 'app-log-detail-dialog',
  imports: [ModalShellComponent, LogIpComponent],
  templateUrl: './log-detail-dialog.component.html',
  styleUrl: './log-detail-dialog.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(keydown)': 'onKeydown($event)' },
})
export class LogDetailDialogComponent {
  private readonly destroyRef = inject(DestroyRef);
  private readonly body = viewChild.required<ElementRef<HTMLElement>>('detailBody');
  readonly event = input.required<LogEvent>();
  readonly timeSettings = input.required<LogTimeSettings>();
  readonly closed = output<void>();
  readonly navigationRequested = output<-1 | 1>();
  readonly description = computed(() => describeLogEvent(this.event()));
  readonly errors = computed(() => describeLogErrors(this.event().errors));
  readonly jsonExpanded = model(false);
  readonly json = computed(() => JSON.stringify(this.event(), null, 2));
  readonly copying = signal(false);
  readonly copyMessage = signal('');
  readonly formattedTime = computed(() => createLogTimeFormatter(this.timeSettings())(this.event().ts));
  readonly response = computed(() => {
    const event = this.event();
    const status = finiteNumber(event.http_status);
    return {
      status,
      count: finiteNumber(event.result?.count),
      duration: finiteNumber(event.duration_ms),
      successful: status !== null && status >= 200 && status < 400,
      failed: status !== null && status >= 400,
    };
  });

  constructor() {
    afterRenderEffect(() => {
      this.event();
      this.copyMessage.set('');
      this.body().nativeElement.scrollTop = 0;
    });
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.defaultPrevented || event.isComposing
      || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const target = event.target;
    if (target instanceof HTMLElement
      && (target.isContentEditable || target.closest('input, textarea, select'))) return;
    if (window.getSelection()?.isCollapsed === false) return;

    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      this.navigationRequested.emit(-1);
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      this.navigationRequested.emit(1);
    }
  }

  toggleJson(event: Event): void {
    this.jsonExpanded.set((event.target as HTMLDetailsElement).open);
    this.copyMessage.set('');
  }

  async copyJson(): Promise<void> {
    if (this.copying()) return;
    this.copying.set(true);
    this.copyMessage.set('');
    const eventId = this.event().id;
    try {
      await navigator.clipboard.writeText(this.json());
    } catch {
      if (!this.destroyRef.destroyed && this.event().id === eventId) {
        this.copyMessage.set('Could not copy JSON. Select the text below and copy it manually.');
      }
    } finally {
      if (!this.destroyRef.destroyed) this.copying.set(false);
    }
  }
}
