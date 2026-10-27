import { computed, inject, Injectable } from '@angular/core';
import { moveItem } from '../../shared/utils/move-item';
import { ColumnMove } from '../../shared/controls/column-settings.component';
import { LOG_COLUMNS, LogColumnId, LogSort, isLogColumnId } from './log-columns';
import { finiteNumber, formatLogFilters, LogQuery } from './log-presenter';
import { LogState } from './log-state';
import { LogEvent } from './log-types';

type CellValue = string | number | null;

export interface LogRow {
  event: LogEvent;
  queries: LogQuery[];
  cells: Record<LogColumnId, CellValue>;
  timestamp: number | null;
}

const COLLATOR = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
const COLUMNS_BY_ID = new Map(LOG_COLUMNS.map(column => [column.id, column]));

export function compareLogRows(left: LogRow, right: LogRow, sort: LogSort): number {
  const leftValue = sort.column === 'time' ? left.timestamp : left.cells[sort.column];
  const rightValue = sort.column === 'time' ? right.timestamp : right.cells[sort.column];
  // Missing measurements always come last, in either direction; zero is data.
  if (leftValue === null && rightValue !== null) return 1;
  if (rightValue === null && leftValue !== null) return -1;
  const comparison = typeof leftValue === 'number' && typeof rightValue === 'number'
    ? leftValue - rightValue
    : COLLATOR.compare(String(leftValue ?? ''), String(rightValue ?? ''));
  if (comparison) return sort.direction === 'asc' ? comparison : -comparison;
  if (sort.column === 'time') {
    const order = COLLATOR.compare(left.event.id, right.event.id);
    return sort.direction === 'asc' ? order : -order;
  }
  return (right.timestamp ?? 0) - (left.timestamp ?? 0)
    || COLLATOR.compare(right.event.id, left.event.id);
}

@Injectable()
export class LogTable {
  private readonly state = inject(LogState);
  readonly sort = computed(() => this.state.saved.value().sort);
  readonly columns = computed(() => this.state.saved.value().columns.order.map(id => COLUMNS_BY_ID.get(id)!));
  readonly visibleIds = computed(() => this.state.saved.value().columns.visible);
  readonly visibleColumns = computed(() => {
    const visible = new Set(this.visibleIds());
    return this.columns().filter(column => visible.has(column.id));
  });
  readonly minWidth = computed(() => this.visibleColumns().reduce((sum, column) => sum + column.width, 0));
  private readonly presentedRows = computed(() => {
    const formatTime = this.state.formatTime();
    const text = (value: string | undefined) => value?.trim() || null;
    return this.state.filtered().map(({ event, description }): LogRow => ({
      event,
      queries: description.queries,
      timestamp: finiteNumber(Date.parse(event.ts)),
      cells: {
        time: formatTime(event.ts),
        request: description.request,
        query: text(description.queries.map(query => `${query.label} ${query.value}`).join('  ')),
        status: finiteNumber(event.http_status),
        results: finiteNumber(event.result?.count),
        duration: finiteNumber(event.duration_ms),
        ip: text(event.ip),
        client: text(event.client),
        filters: text([
          ...description.queries.flatMap(query => query.options.map(option => `${query.label}: ${option}`)),
          ...formatLogFilters(description.filters),
        ].join('; ')),
        reason: text(event.reason),
        id: event.id,
      },
    }));
  });
  readonly rows = computed(() => [...this.presentedRows()].sort((left, right) =>
    compareLogRows(left, right, this.sort())
  ));

  sortBy(column: LogColumnId): void {
    this.state.saved.update(current => {
      const direction = current.sort.column === column && current.sort.direction === 'asc' ? 'desc' : 'asc';
      return { ...current, sort: { column, direction } };
    });
  }

  setVisible(id: string, visible: boolean): void {
    if (!isLogColumnId(id)) return;
    this.state.saved.update(current => ({
      ...current,
      columns: {
        ...current.columns,
        visible: visible
          ? [...new Set([...current.columns.visible, id])]
          : current.columns.visible.filter(column => column !== id),
      },
    }));
  }

  moveColumn(move: ColumnMove): void {
    if (!isLogColumnId(move.id) || !isLogColumnId(move.target) || move.id === move.target) return;
    const id = move.id;
    const target = move.target;
    this.state.saved.update(current => {
      const order = moveItem(current.columns.order, id, target, move.after);
      if (!order) return current;
      return { ...current, columns: { ...current.columns, order } };
    });
  }

  resetSelection(): void {
    this.state.saved.update(current => ({
      ...current,
      columns: {
        ...current.columns,
        visible: LOG_COLUMNS.filter(column => column.defaultVisible).map(column => column.id),
      },
    }));
  }

  resetOrder(): void {
    this.state.saved.update(current => ({
      ...current,
      columns: { ...current.columns, order: LOG_COLUMNS.map(column => column.id) },
    }));
  }
}
