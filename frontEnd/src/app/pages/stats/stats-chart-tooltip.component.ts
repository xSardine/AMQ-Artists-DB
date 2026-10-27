import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import type { Chart, ChartType, TooltipModel } from 'chart.js';

interface ChartTooltipContent {
  title: string[];
  beforeBody: string[];
  body: {
    before: string[];
    lines: string[];
    after: string[];
    color: string | null;
  }[];
  afterBody: string[];
  footer: string[];
  x: number;
  y: number;
}

@Component({
  selector: 'app-stats-chart-tooltip',
  templateUrl: './stats-chart-tooltip.component.html',
  styleUrl: './stats-chart-tooltip.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'display: contents' },
})
export class StatsChartTooltipComponent {
  readonly content = signal<ChartTooltipContent | null>(null);
  private readonly panel = viewChild.required<ElementRef<HTMLElement>>('panel');

  readonly external = <T extends ChartType>({ chart, tooltip }: {
    chart: Chart;
    tooltip: TooltipModel<T>;
  }): void => {
    if (!tooltip.opacity || !tooltip.dataPoints?.length) {
      this.hide();
      return;
    }

    const rect = chart.canvas.getBoundingClientRect();
    this.content.set({
      title: tooltip.title,
      beforeBody: tooltip.beforeBody,
      body: tooltip.body.map((item, index) => {
        const color = tooltip.labelColors[index]?.backgroundColor;
        return {
          ...item,
          color: tooltip.options.displayColors && typeof color === 'string' ? color : null,
        };
      }),
      afterBody: tooltip.afterBody,
      footer: tooltip.footer,
      x: rect.left + tooltip.caretX,
      y: rect.top + tooltip.caretY,
    });
  };

  constructor() {
    afterRenderEffect(() => {
      const content = this.content();
      const panel = this.panel().nativeElement;

      if (!content) {
        if (panel.matches(':popover-open')) panel.hidePopover();
        return;
      }

      if (!panel.matches(':popover-open')) panel.showPopover();

      const edge = 12;
      const gap = 10;
      const { width, height } = panel.getBoundingClientRect();
      const left = content.x + gap + width <= window.innerWidth - edge
        ? content.x + gap
        : content.x - gap - width;
      const top = content.y + gap + height <= window.innerHeight - edge
        ? content.y + gap
        : content.y - gap - height;

      panel.style.left = `${Math.max(edge, Math.min(left, window.innerWidth - width - edge))}px`;
      panel.style.top = `${Math.max(edge, Math.min(top, window.innerHeight - height - edge))}px`;
    });

    const dismiss = () => this.hide();
    document.addEventListener('scroll', dismiss, true);
    window.addEventListener('resize', dismiss);
    inject(DestroyRef).onDestroy(() => {
      document.removeEventListener('scroll', dismiss, true);
      window.removeEventListener('resize', dismiss);
    });
  }

  hide(): void {
    this.content.set(null);
  }
}
