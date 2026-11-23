import { ChangeDetectionStrategy, Component, computed, effect, input, signal } from '@angular/core';

export interface StatsTable {
  headings: string[];
  rows: string[][];
  numericColumns: number[];
  emptyMessage?: string;
}

@Component({
  selector: 'app-stats-table',
  template: `
    <table class="data-table">
      <thead><tr>
        @for (heading of table().headings; track $index) {
          <th scope="col" [class.numeric]="table().numericColumns.includes($index)">{{ heading }}</th>
        }
      </tr></thead>
      <tbody>
        @for (row of rows(); track $index) {
          <tr>@for (cell of row; track $index) {
            <td [class.numeric]="table().numericColumns.includes($index)">{{ cell }}</td>
          }</tr>
        } @empty {
          <tr><td class="empty-state" [attr.colspan]="table().headings.length">{{ table().emptyMessage || 'No data.' }}</td></tr>
        }
      </tbody>
    </table>
    @if (table().rows.length > pageSize) {
      <nav class="table-pagination" aria-label="Table pages">
        <button class="app-button" type="button" (click)="page.set(page() - 1)" [disabled]="page() === 0">Previous</button>
        <span>{{ page() * pageSize + 1 }}–{{ page() * pageSize + rows().length }} of {{ table().rows.length }}</span>
        <button class="app-button" type="button" (click)="page.set(page() + 1)" [disabled]="(page() + 1) * pageSize >= table().rows.length">Next</button>
      </nav>
    }`,
  styleUrl: './stats-table.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'display: contents' },
})
export class StatsTableComponent {
  readonly table = input.required<StatsTable>();
  readonly page = signal(0);
  readonly pageSize = 100;
  readonly rows = computed(() => this.table().rows.slice(this.page() * this.pageSize, (this.page() + 1) * this.pageSize));

  constructor() {
    effect(() => {
      this.table();
      this.page.set(0);
    });
  }
}
