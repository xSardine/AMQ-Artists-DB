import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ToolbarComponent } from '../../shared/layout/toolbar.component';
import { ReviewAccessFormComponent } from './review-access-form.component';
import { ConfirmDialogComponent } from '../../shared/dialogs/confirm-dialog.component';
import { ReviewChangeComponent } from './review-change.component';
import { ReviewSettingsDialogComponent } from './review-settings-dialog.component';
import { ReviewState } from './review-state';
import { formatLocalTimestamp } from '../../shared/utils/date-format';

@Component({
  selector: 'app-review-page',
  imports: [
    FormsModule,
    ToolbarComponent,
    ReviewSettingsDialogComponent,
    ReviewAccessFormComponent,
    ReviewChangeComponent,
    ConfirmDialogComponent
  ],
  providers: [ReviewState],
  templateUrl: './review-page.component.html',
  styleUrl: './review-page.component.css',
  host: { style: 'display: block' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReviewPageComponent {
  readonly state = inject(ReviewState);
  readonly settingsOpen = signal(false);
  readonly formatTimestamp = formatLocalTimestamp;

  toggleIssues(event: Event): void {
    this.state.toggleIssues((event.target as HTMLDetailsElement).open);
  }
}
