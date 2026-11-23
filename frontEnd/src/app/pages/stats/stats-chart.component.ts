import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  ElementRef,
  inject,
  input,
  untracked,
  viewChild,
} from '@angular/core';
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js';
import { ThemeService } from '../../core/theme.service';
import { readStatsChartTheme } from './stats-chart-theme';
import { StatsChartTooltipComponent } from './stats-chart-tooltip.component';
import type { StatsChartConfiguration, StatsChartPoint } from './stats-panels';

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Legend,
  Tooltip,
);

@Component({
  selector: 'app-stats-chart',
  imports: [StatsChartTooltipComponent],
  templateUrl: './stats-chart.component.html',
  styleUrl: './stats-chart.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'display: contents' },
})
export class StatsChartComponent {
  readonly data = input.required<StatsChartConfiguration>();
  readonly description = input.required<string>();
  readonly hasData = computed(() => this.data().data.datasets.some(dataset =>
    dataset.data.some(point => point.y !== null && Number.isFinite(point.y)),
  ));

  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  private readonly tooltip = viewChild.required(StatsChartTooltipComponent);
  private readonly theme = inject(ThemeService);
  private chart?: Chart<'bar' | 'line', StatsChartPoint[], string>;

  constructor() {
    afterRenderEffect(() => {
      const data = this.data();
      this.theme.theme();
      const canvas = this.canvas()?.nativeElement;

      untracked(() => {
        this.tooltip().hide();
        if (!canvas) {
          this.destroyChart();
          return;
        }

        const config = this.withTheme(data);
        if (this.chart && 'type' in this.chart.config && this.chart.config.type !== config.type) {
          this.destroyChart();
        }
        if (this.chart) {
          const previousDatasets = this.chart.data.datasets;
          this.chart.data = {
            ...config.data,
            datasets: config.data.datasets.map((dataset, index) => {
              const previous = previousDatasets[index];
              if (previous?.label === dataset.label) {
                // Keep Chart.js legend visibility when data or theme changes.
                Object.assign(previous, dataset);
                return previous;
              }
              return dataset;
            }),
          };
          this.chart.options = config.options ?? {};
          // Animation is disabled below. A normal update also refreshes shared element colors.
          this.chart.update();
        } else {
          this.chart = new Chart(canvas, config);
        }
      });
    });

    inject(DestroyRef).onDestroy(() => this.destroyChart());
  }

  private withTheme(config: StatsChartConfiguration): StatsChartConfiguration {
    const theme = readStatsChartTheme();
    const { muted, border } = theme;
    const options = config.options ?? {};
    const scales = Object.fromEntries(
      Object.entries(options.scales ?? {}).map(([id, scale]) => [id, {
        ...scale,
        ticks: { ...scale?.ticks, color: muted },
        grid: { ...scale?.grid, color: border },
        border: { ...scale?.border, color: border },
      }]),
    );

    return {
      ...config,
      data: {
        ...config.data,
        datasets: config.data.datasets.map((dataset, index) => {
          const seriesColor = theme.seriesColor(index);
          return { ...dataset, backgroundColor: seriesColor, borderColor: seriesColor };
        }),
      },
      options: {
        ...options,
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        color: muted,
        font: { family: 'Arial, sans-serif', size: 11 },
        scales,
        plugins: {
          ...options.plugins,
          legend: {
            ...options.plugins?.legend,
            labels: { ...options.plugins?.legend?.labels, color: muted },
          },
          tooltip: {
            ...options.plugins?.tooltip,
            enabled: false,
            external: this.tooltip().external,
          },
        },
      },
    };
  }

  private destroyChart(): void {
    this.chart?.destroy();
    this.chart = undefined;
  }
}
