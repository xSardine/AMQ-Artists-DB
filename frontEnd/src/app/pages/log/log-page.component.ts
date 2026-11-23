import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  effect,
  ElementRef,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ColumnSettingsComponent } from '../../shared/controls/column-settings.component';
import { ToolbarComponent } from '../../shared/layout/toolbar.component';
import { LogAccessFormComponent } from './log-access-form.component';
import { LogColumnId } from './log-columns';
import { LogDetailDialogComponent } from './log-detail-dialog.component';
import { LogIpComponent } from './log-ip.component';
import { LogSettingsDialogComponent } from './log-settings-dialog.component';
import { captureLogScroll, LogScrollPosition, restoreLogScroll } from './log-scroll';
import { LogState } from './log-state';
import { LogRow, LogTable } from './log-table';
import { LogEvent } from './log-types';

@Component({
  selector: 'app-log-page',
  imports: [
    FormsModule,
    ColumnSettingsComponent,
    ToolbarComponent,
    LogSettingsDialogComponent,
    LogAccessFormComponent,
    LogDetailDialogComponent,
    LogIpComponent,
  ],
  providers: [LogState, LogTable],
  templateUrl: './log-page.component.html',
  styleUrl: './log-page.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogPageComponent {
  readonly state = inject(LogState);
  readonly table = inject(LogTable);
  readonly settingsOpen = signal(false);
  readonly selectedEvent = signal<LogEvent | null>(null);
  readonly detailsJsonExpanded = signal(false);
  readonly columnsOpen = signal(false);
  private readonly viewport = viewChild<ElementRef<HTMLElement>>('logViewport');
  private scrollPosition: LogScrollPosition | null = null;

  constructor() {
    effect(() => {
      if (!this.state.authenticated()) {
        this.selectedEvent.set(null);
        this.columnsOpen.set(false);
      }
    });
    const subscription = this.state.beforeUpdate.subscribe(() => {
      const viewport = this.viewport()?.nativeElement;
      if (!viewport) return;
      const sort = this.table.sort();
      const follow = this.state.autoScroll() && sort.column === 'time' && !this.selectedEvent();
      this.scrollPosition = captureLogScroll(viewport, follow, sort.direction === 'asc');
    });
    inject(DestroyRef).onDestroy(() => subscription.unsubscribe());
    afterRenderEffect(() => {
      this.table.rows();
      const viewport = this.viewport()?.nativeElement;
      if (viewport && this.scrollPosition) {
        restoreLogScroll(viewport, this.scrollPosition);
        this.scrollPosition = null;
      }
    });
  }

  sortBy(column: LogColumnId): void {
    this.table.sortBy(column);
    const sort = this.table.sort();
    this.scrollPosition = {
      follow: this.state.autoScroll() && sort.column === 'time' && sort.direction === 'asc' ? 'end' : 'start',
      scrollTop: 0,
      anchors: [],
    };
  }

  inspectRow(event: MouseEvent, row: LogRow): void {
    const selection = window.getSelection();
    if (selection && !selection.isCollapsed && selection.anchorNode
      && this.viewport()?.nativeElement.contains(selection.anchorNode)) return;
    this.openEvent(row.event, event.currentTarget as HTMLElement);
  }

  onRowKeydown(event: KeyboardEvent, row: LogRow): void {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    this.openEvent(row.event, event.currentTarget as HTMLElement);
  }

  closeDetails(): void {
    const event = this.selectedEvent();
    const viewport = this.viewport()?.nativeElement;
    const row = event
      ? viewport?.querySelector<HTMLElement>(`[data-event-id="${CSS.escape(event.id)}"]`)
      : null;
    this.selectedEvent.set(null);
    // Arrow navigation can move away from the row that initially opened the modal.
    // Return to the last inspected row, or the viewport if polling removed it.
    (row ?? viewport)?.focus({ preventScroll: true });
  }

  navigateDetails(offset: -1 | 1): void {
    const event = this.selectedEvent();
    if (!event) return;
    const rows = this.table.rows();
    const index = rows.findIndex(row => row.event.id === event.id);
    if (index < 0) return;
    const next = rows[index + offset];
    if (next) this.selectedEvent.set(next.event);
  }

  private openEvent(event: LogEvent, row: HTMLElement): void {
    row.focus({ preventScroll: true });
    this.columnsOpen.set(false);
    this.selectedEvent.set(event);
  }
}
