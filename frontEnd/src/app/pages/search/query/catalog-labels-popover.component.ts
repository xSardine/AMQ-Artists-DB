import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { InfoPopoverComponent } from '../../../shared/controls/info-popover.component';

@Component({
  selector: 'app-catalog-labels-popover',
  imports: [InfoPopoverComponent],
  templateUrl: './catalog-labels-popover.component.html',
  styleUrl: './catalog-labels-popover.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CatalogLabelsPopoverComponent {
  readonly heading = input.required<string>();
  readonly idPrefix = input.required<string>();
  readonly names = input<readonly string[] | null>(null);
  readonly loading = input(false);
  readonly error = input('');
  readonly loadRequested = output<void>();
}
