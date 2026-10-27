import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

@Component({
  selector: 'app-toolbar',
  templateUrl: './toolbar.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'display: contents' },
})
export class ToolbarComponent {
  readonly href = input.required<string>();
  readonly section = input('');
  readonly logoLinkId = input<string>();
  readonly settingsButtonId = input('settings');
  readonly wrapControls = input(false);
  readonly settingsRequested = output<void>();
}
