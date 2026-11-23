import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import type { ReviewChange, ReviewHistoryPage } from '../../shared/contributions/contribution-types';
import { FIELD_LABELS, isArtistId, profileUrl } from '../../shared/contributions/contribution-fields';
import { displayValue, recordContext } from '../../shared/contributions/contribution-format';
import { formatLocalTimestamp } from '../../shared/utils/date-format';
import type { ReviewDraft, ReviewDraftPatch } from './review-state';

@Component({
  selector: 'app-review-change',
  imports: [FormsModule],
  templateUrl: './review-change.component.html',
  styleUrl: './review-change.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'display: contents' },
})
export class ReviewChangeComponent {
  readonly change = input.required<Readonly<ReviewChange>>();
  readonly draft = input.required<Readonly<ReviewDraft>>();
  readonly busy = input(false);
  readonly loadedRevision = input(0);
  readonly historyId = input<number | null>(null);
  readonly history = input<ReviewHistoryPage | null>(null);
  readonly historyOffset = input(0);
  readonly historyLoading = input(false);
  readonly edited = output<ReviewDraftPatch>();
  readonly undoRequested = output<ReviewChange>();
  readonly historyToggled = output<boolean>();
  readonly historyRequested = output<number>();
  readonly labels = FIELD_LABELS;
  readonly display = displayValue;
  readonly recordContext = recordContext;
  readonly profileUrl = profileUrl;
  readonly isArtistId = isArtistId;
  readonly formatTimestamp = formatLocalTimestamp;
  readonly maxArtistId = Number.MAX_SAFE_INTEGER;
  readonly historyPageSize = 10;

  readonly waiting = computed(() => this.change().field_revision > this.loadedRevision());
  readonly commentOpen = signal(false);

  toggleHistory(event: Event): void {
    this.historyToggled.emit((event.target as HTMLDetailsElement).open);
  }

  toggleComment(event: Event): void {
    this.commentOpen.set((event.target as HTMLDetailsElement).open);
  }
}
