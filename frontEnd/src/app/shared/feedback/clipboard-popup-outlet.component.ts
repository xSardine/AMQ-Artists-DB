import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ClipboardService } from './clipboard.service';

@Component({
  selector: 'app-clipboard-popup-outlet',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (clipboard.popup(); as popup) {
      <div class="app-clipboard-popup" [style.left]="popup.left" [style.top]="popup.top">
        Copied
      </div>
    }
  `,
})
export class ClipboardPopupOutletComponent {
  readonly clipboard = inject(ClipboardService);
}
