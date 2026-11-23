import { computed, effect, inject, Injectable, signal, untracked } from '@angular/core';
import { moveItem } from '../../../shared/utils/move-item';
import { BrowserStorage } from '../../../core/browser-storage.service';
import { TABLE_SETTINGS } from './table-settings';
import { SearchPreferencesService } from '../settings/search-preferences.service';
import { SongWorkspaceStore } from '../songs/song-workspace.store';
import { compareSongsByColumn, SONG_TABLE_COLUMNS, type CustomSongColumnDefinition, type SongColumnDefinition, type SongColumnPosition } from './song-table-columns';

type SongColumnVisibility = Record<string, boolean>;
type SongTableSort = {
  column: string;
  ascending: boolean;
};

@Injectable()
export class SongTableController {
  private readonly workspace = inject(SongWorkspaceStore);
  readonly saved = inject(BrowserStorage).record(TABLE_SETTINGS);
  private readonly preferences = inject(SearchPreferencesService);
  private readonly columnsSignal = signal<readonly SongColumnDefinition[]>(
    SONG_TABLE_COLUMNS,
  );
  private readonly columnOrderSignal = computed(() => [...new Set([
    ...this.saved.value().order,
    ...this.columnsSignal().map(column => column.id),
  ])]);
  private readonly visibilitySignal = computed(() => this.saved.value().visibility);

  readonly availableColumns = computed(() => orderColumns(
    this.columnsSignal(),
    this.columnOrderSignal(),
  ));
  readonly visibility = this.visibilitySignal;
  readonly visibleColumns = computed(() =>
    this.availableColumns().filter((column) => this.isVisible(column.id)),
  );
  readonly sortState = computed((): SongTableSort | null => {
    const sort = this.workspace.sortState();
    if (!sort) return null;

    const column = this.findColumn(sort.column);
    return column ? { column: column.id, ascending: sort.ascending } : null;
  });

  constructor() {
    let previousLanguage = this.preferences.preferences().animeTitleLanguage;
    effect(() => {
      const language = this.preferences.preferences().animeTitleLanguage;
      if (language !== previousLanguage && untracked(this.sortState)?.column === 'anime') {
        this.clearSort();
      }
      previousLanguage = language;
    });
  }

  /** Registers a userscript column and returns an idempotent unregister callback. */
  registerColumn(
    definition: CustomSongColumnDefinition,
    position?: SongColumnPosition,
  ): () => void {
    this.validateColumnDefinition(definition);
    if (this.findColumn(definition.id)) {
      throw new Error(`A table column with id "${definition.id}" already exists.`);
    }
    this.validateColumnPosition(position);

    const registeredColumn = Object.freeze({
      ...definition,
      header: definition.header.trim(),
      visibilityLabel: definition.visibilityLabel?.trim() || undefined,
    }) as SongColumnDefinition;
    const definitions = insertColumn(
      this.columnsSignal(),
      registeredColumn,
      position,
    );
    const currentOrder = this.columnOrderSignal();
    const order = currentOrder.includes(registeredColumn.id)
      ? currentOrder
      : insertColumnId(currentOrder, registeredColumn.id, position);

    this.columnsSignal.set(definitions);
    if (order !== currentOrder) {
      this.saveColumnOrder(order);
    }

    return () => {
      if (!this.columnsSignal().includes(registeredColumn)) return;

      this.columnsSignal.update((columns) =>
        columns.filter((column) => column !== registeredColumn),
      );
      if (this.workspace.sortState()?.column === registeredColumn.id) {
        this.workspace.clearSort();
      }
    };
  }

  isVisible(columnId: string): boolean {
    const column = this.findColumn(columnId);
    return column
      ? this.visibilitySignal()[columnId] ?? column.defaultVisible
      : false;
  }

  setVisible(columnId: string, visible: boolean): void {
    this.requireColumn(columnId);
    this.saved.update(current => ({
      ...current,
      visibility: { ...current.visibility, [columnId]: visible },
    }));
  }

  updateVisibility(patch: Partial<SongColumnVisibility>): void {
    const visibility: SongColumnVisibility = {};
    for (const column of this.availableColumns()) {
      const value = patch[column.id];
      if (typeof value === 'boolean') visibility[column.id] = value;
    }
    this.saved.update(current => ({ ...current, visibility: { ...current.visibility, ...visibility } }));
  }

  resetVisibility(): void {
    this.saveVisibility({});
  }

  moveColumn(
    movedColumnId: string,
    targetColumnId: string,
    insertAfter: boolean,
  ): boolean {
    if (movedColumnId === targetColumnId) return false;
    this.requireColumn(movedColumnId);
    this.requireColumn(targetColumnId);

    const order = moveItem(this.columnOrderSignal(), movedColumnId, targetColumnId, insertAfter);
    if (!order) return false;

    this.saveColumnOrder(order);
    return true;
  }

  resetColumnOrder(): void {
    this.saveColumnOrder(this.columnsSignal().map(column => column.id));
  }

  sort(columnId: string): boolean {
    const songs = this.workspace.songs();
    const column = this.findColumn(columnId);
    if (!songs || !column?.sort) return false;

    const currentSort = this.sortState();
    const ascending = currentSort?.column === columnId ? !currentSort.ascending : true;
    const direction = ascending ? 1 : -1;
    const language = this.preferences.preferences().animeTitleLanguage;
    return this.workspace.sort(
      (left, right) => direction * compareSongsByColumn(left, right, column, language),
      { column: columnId, ascending },
    );
  }

  clearSort(): void {
    this.workspace.clearSort();
  }

  private findColumn(columnId: string): SongColumnDefinition | undefined {
    return this.columnsSignal().find((column) => column.id === columnId);
  }

  private requireColumn(columnId: string): SongColumnDefinition {
    const column = this.findColumn(columnId);
    if (!column) throw new RangeError(`Unknown table column: ${columnId}`);
    return column;
  }

  private saveColumnOrder(order: readonly string[]): void {
    this.saved.update(current => ({ ...current, order: [...order] }));
  }

  private saveVisibility(visibility: SongColumnVisibility): void {
    this.saved.update(current => ({ ...current, visibility }));
  }

  private validateColumnDefinition(
    definition: CustomSongColumnDefinition,
  ): void {
    if (!definition || typeof definition !== 'object') {
      throw new TypeError('A table column definition is required.');
    }
    if (typeof definition.id !== 'string' || !/^[a-z][a-z0-9-]*$/.test(definition.id)) {
      throw new TypeError('Custom table column ids must start with a letter and contain only lowercase letters, numbers, and hyphens.');
    }
    if (typeof definition.header !== 'string' || !definition.header.trim()) {
      throw new TypeError('Custom table column headers cannot be empty.');
    }
    if (typeof definition.defaultVisible !== 'boolean') {
      throw new TypeError('Custom table columns must specify defaultVisible.');
    }
    if (
      definition.visibilityLabel !== undefined
      && (typeof definition.visibilityLabel !== 'string' || !definition.visibilityLabel.trim())
    ) {
      throw new TypeError('Custom table column visibility labels cannot be empty.');
    }
    for (const property of ['centered', 'nowrap'] as const) {
      if (definition[property] !== undefined && typeof definition[property] !== 'boolean') {
        throw new TypeError(`Custom table column ${property} must be a boolean.`);
      }
    }

    const hasDisplay = typeof definition.display === 'function';
    const hasRenderer = typeof definition.renderCell === 'function';
    if (hasDisplay === hasRenderer) {
      throw new TypeError('Custom table columns must define exactly one of display or renderCell.');
    }
    if (definition.copy !== undefined && typeof definition.copy !== 'function') {
      throw new TypeError('Custom table column copy must be a function.');
    }
    if (definition.copy && !hasDisplay) {
      throw new TypeError('Custom table column copy requires display.');
    }
    if (definition.sort !== undefined && typeof definition.sort !== 'function') {
      throw new TypeError('Custom table column sort must be a function.');
    }
  }

  private validateColumnPosition(position?: SongColumnPosition): void {
    if (position === undefined) return;
    if (!position || typeof position !== 'object') {
      throw new TypeError('A custom table column position must specify before or after.');
    }

    const before = 'before' in position ? position.before : undefined;
    const after = 'after' in position ? position.after : undefined;
    if ((typeof before === 'string') === (typeof after === 'string')) {
      throw new TypeError('A custom table column position must specify exactly one of before or after.');
    }

    const targetId = typeof before === 'string' ? before : after;
    if (!targetId || !this.findColumn(targetId)) {
      throw new RangeError(`Unknown table column position target: ${String(targetId)}`);
    }
  }
}

function orderColumns(
  columns: readonly SongColumnDefinition[],
  order: readonly string[],
): readonly SongColumnDefinition[] {
  const byId = new Map(columns.map((column) => [column.id, column]));
  const ordered: SongColumnDefinition[] = [];

  for (const id of order) {
    const column = byId.get(id);
    if (!column) continue;
    ordered.push(column);
    byId.delete(id);
  }

  ordered.push(...byId.values());
  return ordered;
}

function insertColumn(
  columns: readonly SongColumnDefinition[],
  column: SongColumnDefinition,
  position?: SongColumnPosition,
): readonly SongColumnDefinition[] {
  const next = [...columns];
  if (!position) {
    next.push(column);
    return next;
  }

  const targetId = ('before' in position ? position.before : position.after)!;
  let index = next.findIndex((candidate) => candidate.id === targetId);
  if ('after' in position) index += 1;
  next.splice(index, 0, column);
  return next;
}

function insertColumnId(
  order: readonly string[],
  columnId: string,
  position?: SongColumnPosition,
): string[] {
  const next = [...order];
  if (!position) {
    next.push(columnId);
    return next;
  }

  const targetId = ('before' in position ? position.before : position.after)!;
  let index = next.indexOf(targetId);
  if ('after' in position) index += 1;
  next.splice(index, 0, columnId);
  return next;
}

