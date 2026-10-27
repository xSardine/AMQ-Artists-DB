import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  ElementRef,
  inject,
  input,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { ArcElement, Chart, DoughnutController, Tooltip } from 'chart.js';
import type { TooltipItem } from 'chart.js';
import { ThemeService } from '../../core/theme.service';
import { readStatsChartTheme } from './stats-chart-theme';
import { formatNumber, formatShare } from './stats-tables';
import { StatsChartTooltipComponent } from './stats-chart-tooltip.component';

Chart.register(ArcElement, DoughnutController, Tooltip);

@Component({
  selector: 'app-stats-composition',
  imports: [StatsChartTooltipComponent],
  templateUrl: './stats-composition.component.html',
  styleUrl: './stats-composition.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatsCompositionComponent {
  readonly values = input<Record<string, number>>();
  readonly total = input.required<number>();
  readonly colors = signal<string[]>([]);
  readonly rows = computed(() => Object.entries(this.values() ?? {}).map(([label, count]) => ({
    label,
    count,
    formattedCount: formatNumber(count),
    share: count > 0 && count / this.total() < 0.001
      ? '<0.1%'
      : formatShare(count, this.total()),
  })));
  readonly hasData = computed(() => this.rows().some(row => row.count > 0));

  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  private readonly tooltip = viewChild.required(StatsChartTooltipComponent);
  private readonly theme = inject(ThemeService);
  private chart?: Chart<'doughnut', number[], string>;

  constructor() {
    afterRenderEffect(() => {
      const rows = this.rows();
      this.theme.theme();
      const canvas = this.canvas()?.nativeElement;

      untracked(() => {
        const theme = readStatsChartTheme();
        const colors = rows.map((_, index) => theme.seriesColor(index));
        this.colors.set(colors);
        this.tooltip().hide();

        if (!canvas) {
          this.destroyChart();
          return;
        }

        const data = {
          labels: rows.map(row => row.label),
          datasets: [{
            data: rows.map(row => row.count),
            backgroundColor: colors,
            borderWidth: 0,
            hoverOffset: 3,
          }],
        };
        const options = {
          responsive: true,
          maintainAspectRatio: false,
          animation: false as const,
          cutout: '68%',
          layout: { padding: 3 },
          plugins: {
            legend: { display: false },
            tooltip: {
              enabled: false,
              external: this.tooltip().external,
              callbacks: {
                label: (context: TooltipItem<'doughnut'>) => {
                  const row = rows[context.dataIndex];
                  return `${row.formattedCount} (${row.share})`;
                },
              },
            },
          },
        };

        if (this.chart) {
          this.chart.data = data;
          this.chart.options = options;
          this.chart.update();
        } else {
          this.chart = new Chart<'doughnut', number[], string>(canvas, {
            type: 'doughnut',
            data,
            options,
          });
        }
      });
    });

    inject(DestroyRef).onDestroy(() => this.destroyChart());
  }

  private destroyChart(): void {
    this.chart?.destroy();
    this.chart = undefined;
  }
}
