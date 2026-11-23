import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, inject, input, output, viewChild } from '@angular/core';

let nextPopoverId = 0;

@Component({
  selector: 'app-info-popover',
  templateUrl: './info-popover.component.html',
  styleUrl: './info-popover.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InfoPopoverComponent {
  readonly label = input.required<string>();
  readonly buttonId = input<string>();
  readonly opening = output<void>();
  readonly popoverId = `app-info-popover-${++nextPopoverId}`;
  private readonly button = viewChild.required<ElementRef<HTMLButtonElement>>('button');
  private readonly panel = viewChild.required<ElementRef<HTMLElement>>('panel');

  constructor() {
    const dismiss = (event: Event) => {
      const panel = this.panel().nativeElement;
      const insidePanel = event.target instanceof Node && panel.contains(event.target);
      if (panel.matches(':popover-open') && !insidePanel) {
        panel.hidePopover();
      }
    };
    document.addEventListener('scroll', dismiss, true);
    window.addEventListener('resize', dismiss);
    inject(DestroyRef).onDestroy(() => {
      document.removeEventListener('scroll', dismiss, true);
      window.removeEventListener('resize', dismiss);
    });
  }

  beforeToggle(event: Event): void {
    if ((event as ToggleEvent).newState !== 'open') return;
    this.opening.emit();
    const rect = this.button().nativeElement.getBoundingClientRect();
    const panel = this.panel().nativeElement;
    const edge = 12;
    const gap = 6;
    const width = Math.min(300, window.innerWidth - edge * 2);
    const below = window.innerHeight - rect.bottom - gap - edge;
    const above = rect.top - gap - edge;
    const showBelow = below >= Math.min(180, above);
    panel.style.left = `${Math.max(edge, Math.min(rect.left, window.innerWidth - width - edge))}px`;
    panel.style.top = showBelow ? `${rect.bottom + gap}px` : 'auto';
    panel.style.bottom = showBelow ? 'auto' : `${window.innerHeight - rect.top + gap}px`;
    panel.style.maxHeight = `${Math.max(0, showBelow ? below : above)}px`;
  }
}
