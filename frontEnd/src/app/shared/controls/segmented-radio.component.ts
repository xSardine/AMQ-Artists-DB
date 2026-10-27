import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

export interface SegmentedRadioOption<Id extends string> {
  readonly id: Id;
  readonly label: string;
}

let nextRadioGroupId = 0;

@Component({
  selector: 'app-segmented-radio',
  template: `
    <div class="segmented-radio-options" role="radiogroup" [attr.aria-label]="label()"
      [style.--option-count]="options().length">
      @for (option of options(); track option.id) {
        <label class="segmented-radio-option" [class.is-selected]="value() === option.id">
          <input type="radio" [name]="name()" [value]="option.id"
            [attr.id]="idPrefix() ? idPrefix() + '-' + option.id.toLowerCase() : null"
            [checked]="value() === option.id" (change)="valueChange.emit(option.id)">
          <span>{{ option.label }}</span>
        </label>
      }
    </div>
  `,
  styleUrl: './segmented-radio.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SegmentedRadioComponent<Id extends string> {
  readonly options = input.required<readonly SegmentedRadioOption<Id>[]>();
  readonly value = input.required<Id>();
  readonly label = input.required<string>();
  readonly name = input(`segmented-radio-${++nextRadioGroupId}`);
  readonly idPrefix = input<string>();
  readonly valueChange = output<Id>();
}
