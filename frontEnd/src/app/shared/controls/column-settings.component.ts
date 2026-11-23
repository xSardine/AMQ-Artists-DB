import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  Injector,
  input,
  model,
  output,
  signal,
  viewChild,
} from '@angular/core';

export interface ColumnOption {
  id: string;
  header: string;
  visibilityLabel?: string;
}

export interface ColumnMove {
  id: string;
  target: string;
  after: boolean;
}

@Component({
  selector: 'app-column-settings',
  templateUrl: './column-settings.component.html',
  styleUrl: './column-settings.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(document:click)': 'onDocumentClick($event)',
    '(document:keydown.escape)': 'onEscape($event)',
  },
})
export class ColumnSettingsComponent {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);
  private readonly toggle = viewChild.required<ElementRef<HTMLButtonElement>>('toggle');
  readonly columns = input.required<readonly ColumnOption[]>();
  readonly visibleIds = input.required<readonly string[]>();
  readonly idPrefix = input('column-settings');
  readonly primary = input(false);
  readonly open = model(false);
  readonly visibilityChanged = output<{ id: string; visible: boolean }>();
  readonly moved = output<ColumnMove>();
  readonly selectionReset = output<void>();
  readonly orderReset = output<void>();
  readonly visible = computed(() => new Set(this.visibleIds()));
  readonly drag = signal<ColumnMove | null>(null);

  constructor() {
    effect(() => {
      if (!this.open()) this.drag.set(null);
    });
  }

  onDocumentClick(event: MouseEvent): void {
    if (event.target instanceof Node && !this.host.nativeElement.contains(event.target)) {
      this.open.set(false);
    }
  }

  onEscape(event: Event): void {
    if (!this.open()) return;
    event.preventDefault();
    this.open.set(false);
    this.toggle().nativeElement.focus();
  }

  setVisible(id: string, event: Event): void {
    this.visibilityChanged.emit({ id, visible: (event.target as HTMLInputElement).checked });
  }

  startDrag(event: DragEvent, id: string): void {
    this.drag.set({ id, target: id, after: false });
    event.stopPropagation();
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', id);
    }
  }

  dragOver(event: DragEvent, target: string): void {
    const drag = this.drag();
    if (!drag || drag.id === target) return;
    event.preventDefault();
    this.drag.set({ ...drag, target, after: this.isAfter(event) });
    if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
  }

  drop(event: DragEvent, target: string): void {
    const drag = this.drag();
    if (!drag) return;
    event.preventDefault();
    event.stopPropagation();
    const currentIds = new Set(this.columns().map(column => column.id));
    if (drag.id !== target && currentIds.has(drag.id) && currentIds.has(target)) {
      this.moved.emit({ id: drag.id, target, after: this.isAfter(event) });
    }
    this.drag.set(null);
  }

  moveWithKeyboard(event: KeyboardEvent, id: string): void {
    if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return;
    event.preventDefault();
    const index = this.columns().findIndex(column => column.id === id);
    if (index < 0) return;
    const after = event.key === 'ArrowDown';
    const target = this.columns()[index + (after ? 1 : -1)];
    if (!target) return;
    this.moved.emit({ id, target: target.id, after });
    afterNextRender(() => {
      const handles = this.host.nativeElement.querySelectorAll<HTMLButtonElement>('[data-column-id]');
      Array.from(handles).find(handle => handle.dataset['columnId'] === id)?.focus({ preventScroll: true });
    }, { injector: this.injector });
  }

  private isAfter(event: DragEvent): boolean {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    return event.clientY > rect.top + rect.height / 2;
  }
}
