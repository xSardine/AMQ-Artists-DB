import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-log-ip',
  template: `
    {{ text() || '—' }}
    @if (color(); as color) {
      <span class="ip-color" [style.background-color]="color" [title]="color" aria-hidden="true"></span>
    }
  `,
  styles: `
    .ip-color {
      display: inline-block;
      width: 10px;
      height: 10px;
      margin-left: 4px;
      border: 1px solid var(--border);
      vertical-align: -1px;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogIpComponent {
  readonly value = input<string>();
  readonly text = computed(() => this.value()?.trim() ?? '');
  readonly color = computed(() => /^[0-9a-f]{6}$/i.test(this.text()) ? `#${this.text()}` : null);
}
