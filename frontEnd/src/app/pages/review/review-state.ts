import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { type ContributionField, normalizeValue } from '../../shared/contributions/contribution-fields';
import type {
  ContributionOperation,
  ReviewAction,
  ReviewChange,
  ReviewHistoryPage,
  ReviewIssuePage,
  ReviewQueue,
  ReviewSubmission,
} from '../../shared/contributions/contribution-types';
import { ApiClient, errorMessage, ApiError } from '../../core/api-client.service';
import { AccessSession } from '../../core/access-session';

export interface ReviewDraft {
  submissionId: number;
  field: ContributionField;
  operation: ContributionOperation;
  action: ReviewAction;
  value: string | number | null;
  oldValue: string | null;
  comment: string;
  reviewVersion: number;
  fieldRevision: number;
  stale: boolean;
}

export type ReviewDraftPatch = Partial<Pick<ReviewDraft, 'action' | 'value' | 'comment'>>;

@Injectable()
export class ReviewState {
  private readonly api = inject(ApiClient);
  readonly authenticated = signal(false);
  readonly reviewer = signal('');
  readonly queue = signal<ReviewQueue | null>(null);
  readonly submission = signal<ReviewSubmission | null>(null);
  readonly expandedSubmission = signal<number | null>(null);
  readonly changeOffset = signal(0);
  readonly historyChange = signal<number | null>(null);
  readonly historyOffset = signal(0);
  readonly history = signal<ReviewHistoryPage | null>(null);
  readonly historyLoading = signal(false);
  readonly issuesOpen = signal(false);
  readonly issueOffset = signal(0);
  readonly issues = signal<ReviewIssuePage | null>(null);
  readonly issuesLoading = signal(false);
  readonly pageHistory = signal<(number | undefined)[]>([]);
  readonly queueLoading = signal(false);
  readonly detailLoading = signal(false);
  readonly saving = signal(false);
  readonly loggingOut = signal(false);
  readonly busy = computed(() => this.queueLoading() || this.saving() || this.loggingOut());
  readonly error = signal('');
  readonly message = signal('');
  readonly undoTarget = signal<ReviewChange | null>(null);
  readonly commentOpen = signal(false);
  readonly visibleChanges = computed(() => this.submission()?.changes.slice(this.changeOffset(), this.changeOffset() + 5) || []);
  readonly drafts = signal(new Map<number, ReviewDraft>());
  private readonly draftCounts = computed(() => {
    const counts = new Map<number, {
      pending: number;
      stale: boolean;
    }>();
    for (const draft of this.drafts().values()) {
      const current = counts.get(draft.submissionId) || {
        pending: 0,
        stale: false
      };
      current.pending++;
      current.stale ||= draft.stale;
      counts.set(draft.submissionId, current);
    }
    return counts;
  });
  status = 'pending';
  kind = '';
  filter = '';
  private defaults = new Map<number, ReviewDraft>();
  private requests = new Map<string, AbortController>();
  private currentBefore?: number;
  private sessionGeneration = 0;

  constructor() {
    inject(DestroyRef).onDestroy(() => this.cancelRequests());
    const generation = this.sessionGeneration;
    const request = this.request('session');
    void this.api.requestOnce<AccessSession>('/api/review/session', { authenticated: true, signal: request.signal })
      .then(session => {
        if (!request.signal.aborted && generation === this.sessionGeneration && session.authenticated) {
          this.onLogin(session);
        }
      })
      .catch(() => { });
  }

  private request(key: string): AbortController {
    this.requests.get(key)?.abort();
    const request = new AbortController();
    this.requests.set(key, request);
    return request;
  }

  private cancelRequests(): void {
    for (const request of this.requests.values()) request.abort();
    this.requests.clear();
  }

  private clearPrivateState(): void {
    this.sessionGeneration++;
    this.cancelRequests();
    this.authenticated.set(false);
    this.reviewer.set('');
    this.queue.set(null);
    this.submission.set(null);
    this.expandedSubmission.set(null);
    this.history.set(null);
    this.historyChange.set(null);
    this.issues.set(null);
    this.issuesOpen.set(false);
    this.drafts.set(new Map());
    this.defaults.clear();
    this.pageHistory.set([]);
    this.currentBefore = undefined;
    this.undoTarget.set(null);
    this.queueLoading.set(false);
    this.detailLoading.set(false);
    this.historyLoading.set(false);
    this.issuesLoading.set(false);
    this.saving.set(false);
  }

  private failed(error: unknown): void {
    if (error instanceof ApiError && error.status === 401) {
      this.clearPrivateState();
    } else {
      this.error.set(errorMessage(error));
    }
  }

  onLogin(session: AccessSession): void {
    this.sessionGeneration++;
    this.authenticated.set(session.authenticated);
    this.reviewer.set(session.name);
    if (session.authenticated) {
      void this.load();
    }
  }

  private async fetchQueue(before?: number): Promise<boolean> {
    const request = this.request('queue');
    this.queueLoading.set(true);
    this.error.set('');
    try {
      const query = new URLSearchParams({
        status: this.status,
        limit: '10'
      });
      if (before) {
        query.set('before', String(before));
      }
      if (this.kind) {
        query.set('kind', this.kind);
      }
      if (this.filter.trim()) {
        query.set('search', this.filter.trim());
      }
      const result = await this.api.requestOnce<ReviewQueue>('/api/review/submissions?' + query, { authenticated: true, signal: request.signal });
      if (request.signal.aborted) {
        return false;
      }
      this.queue.set(result);
      this.currentBefore = before;
      const current = this.expandedSubmission();
      const id = result.submissions.some(item => item.id === current) ? current : result.submissions[0]?.id ?? null;
      this.expandedSubmission.set(id);
      if (id !== null) {
        await this.loadSubmission(id);
      } else {
        this.requests.get('detail')?.abort();
        this.submission.set(null);
        this.detailLoading.set(false);
      }
      if (this.issuesOpen() && result.issue_count) {
        await this.loadIssues(0);
      }
      return !request.signal.aborted;
    } catch (error) {
      if (!request.signal.aborted) {
        this.failed(error);
      }
      return false;
    } finally {
      if (!request.signal.aborted) {
        this.queueLoading.set(false);
      }
    }
  }

  async load(): Promise<void> {
    if (await this.fetchQueue()) {
      this.pageHistory.set([]);
    }
  }

  async refresh(): Promise<void> {
    await this.fetchQueue(this.currentBefore);
  }

  async older(): Promise<void> {
    const before = this.queue()?.next_before;
    if (this.busy() || before == null) {
      return;
    }
    const previous = this.currentBefore;
    if (await this.fetchQueue(before)) {
      this.pageHistory.update(pages => [...pages, previous]);
    }
  }

  async newer(): Promise<void> {
    const pages = this.pageHistory();
    if (this.busy() || !pages.length) {
      return;
    }
    if (await this.fetchQueue(pages.at(-1))) {
      this.pageHistory.set(pages.slice(0, -1));
    }
  }

  async toggleSubmission(id: number): Promise<void> {
    if (this.expandedSubmission() === id) {
      this.requests.get('detail')?.abort();
      this.expandedSubmission.set(null);
      this.submission.set(null);
      this.detailLoading.set(false);
      this.closeHistory();
      return;
    }
    this.expandedSubmission.set(id);
    this.changeOffset.set(0);
    await this.loadSubmission(id);
  }

  private async loadSubmission(id: number): Promise<void> {
    const request = this.request('detail');
    this.detailLoading.set(true);
    this.submission.set(null);
    this.closeHistory();
    this.commentOpen.set(false);
    try {
      const detail = await this.api.requestOnce<ReviewSubmission>('/api/review/submissions/' + id, { authenticated: true, signal: request.signal });
      if (request.signal.aborted || this.expandedSubmission() !== id) {
        return;
      }
      this.defaults.clear();
      const drafts = new Map(this.drafts());
      for (const change of detail.changes) {
        if (change.review_status === 'approved') {
          drafts.delete(change.id);
        }
        const draft = drafts.get(change.id);
        if (draft) {
          drafts.set(change.id, {
            ...draft,
            stale: draft.reviewVersion !== change.review_version || draft.fieldRevision !== change.field_revision,
          });
        }
        this.defaults.set(change.id, {
          submissionId: id,
          field: change.field,
          operation: change.operation,
          action: '',
          value: change.reviewed_value.value,
          oldValue: change.reviewed_value.old_value,
          comment: '',
          reviewVersion: change.review_version,
          fieldRevision: change.field_revision,
          stale: false,
        });
      }
      this.drafts.set(drafts);
      this.changeOffset.set(Math.min(this.changeOffset(), Math.max(0, Math.ceil(detail.changes.length / 5) - 1) * 5));
      this.submission.set(detail);
    } catch (error) {
      if (!request.signal.aborted) {
        this.failed(error);
      }
    } finally {
      if (!request.signal.aborted) {
        this.detailLoading.set(false);
      }
    }
  }

  draftFor(change: ReviewChange): ReviewDraft {
    return this.drafts().get(change.id) || this.defaults.get(change.id)!;
  }

  updateDraft(change: ReviewChange, patch: ReviewDraftPatch): void {
    const drafts = new Map(this.drafts());
    const next = {
      ...this.draftFor(change),
      ...patch,
      stale: false,
      reviewVersion: change.review_version,
      fieldRevision: change.field_revision,
    };
    this.defaults.set(change.id, next);
    if (next.action) {
      drafts.set(change.id, next);
    } else {
      drafts.delete(change.id);
    }
    this.drafts.set(drafts);
  }

  pendingCount(submissionId: number): number {
    return this.draftCounts().get(submissionId)?.pending || 0;
  }

  stale(submissionId: number): boolean {
    return this.draftCounts().get(submissionId)?.stale || false;
  }

  approveAll(): void {
    const submission = this.submission();
    if (this.busy() || !submission) {
      return;
    }
    const drafts = new Map(this.drafts());
    for (const change of submission.changes) {
      if (change.review_status === 'approved' || change.conflict) {
        continue;
      }
      const draft = this.draftFor(change);
      drafts.set(change.id, {
        ...draft,
        action: 'approve',
        stale: false,
        reviewVersion: change.review_version,
        fieldRevision: change.field_revision,
      });
    }
    this.drafts.set(drafts);
  }

  moveChanges(direction: number): void {
    const count = this.submission()?.changes.length || 0;
    this.changeOffset.set(Math.max(0, Math.min(Math.max(0, Math.ceil(count / 5) - 1) * 5, this.changeOffset() + direction * 5)));
    this.closeHistory();
  }

  private closeHistory(): void {
    this.requests.get('history')?.abort();
    this.historyChange.set(null);
    this.history.set(null);
    this.historyOffset.set(0);
    this.historyLoading.set(false);
  }

  async loadHistory(changeId: number, offset = 0): Promise<void> {
    const request = this.request('history');
    this.historyChange.set(changeId);
    this.historyOffset.set(offset);
    this.historyLoading.set(true);
    this.history.set(null);
    try {
      const result = await this.api.requestOnce<ReviewHistoryPage>('/api/review/changes/' + changeId + '/history?offset=' + offset + '&limit=10', { authenticated: true, signal: request.signal });
      if (!request.signal.aborted) {
        this.history.set(result);
      }
    } catch (error) {
      if (!request.signal.aborted) {
        this.failed(error);
      }
    } finally {
      if (!request.signal.aborted) {
        this.historyLoading.set(false);
      }
    }
  }

  toggleHistory(changeId: number, open: boolean): void {
    if (open && this.historyChange() !== changeId) {
      void this.loadHistory(changeId);
    } else if (!open && this.historyChange() === changeId) {
      this.closeHistory();
    }
  }

  async loadIssues(offset = 0): Promise<void> {
    const request = this.request('issues');
    this.issueOffset.set(offset);
    this.issuesLoading.set(true);
    this.issues.set(null);
    try {
      const result = await this.api.requestOnce<ReviewIssuePage>('/api/review/issues?offset=' + offset + '&limit=10', { authenticated: true, signal: request.signal });
      if (!request.signal.aborted) {
        this.issues.set(result);
      }
    } catch (error) {
      if (!request.signal.aborted) {
        this.failed(error);
      }
    } finally {
      if (!request.signal.aborted) {
        this.issuesLoading.set(false);
      }
    }
  }

  toggleIssues(open: boolean): void {
    this.issuesOpen.set(open);
    if (open) {
      void this.loadIssues();
    } else {
      this.requests.get('issues')?.abort();
      this.issuesLoading.set(false);
    }
  }

  async save(submissionId: number): Promise<void> {
    if (this.busy() || this.stale(submissionId)) {
      return;
    }
    const selected = [...this.drafts()].filter(([, draft]) => draft.submissionId === submissionId);
    if (!selected.length) {
      return;
    }
    const request = this.request('write');
    this.saving.set(true);
    this.error.set('');
    this.message.set('');
    try {
      const decisions = selected.map(([id, draft]) => ({
        change_id: id,
        action: draft.action,
        expected_review_version: draft.reviewVersion,
        expected_field_revision: draft.fieldRevision,
        comment: draft.comment,
        payload: draft.action === 'approve' ? {
          value: draft.operation === 'clear' ? null : normalizeValue(draft.field, draft.value),
          old_value: draft.operation === 'replace_alias' ? draft.oldValue : null,
        } : null,
      }));
      await this.api.requestOnce('/api/review/decisions', {
        authenticated: true,
        method: 'POST',
        body: { decisions },
        signal: request.signal
      });
      if (request.signal.aborted) {
        return;
      }
      const drafts = new Map(this.drafts());
      selected.forEach(([id]) => drafts.delete(id));
      this.drafts.set(drafts);
      this.message.set('Decisions saved. Approved changes take effect after a server restart.');
      await this.refresh();
    } catch (error) {
      if (!request.signal.aborted) {
        this.failed(error);
      }
    } finally {
      if (!request.signal.aborted) {
        this.saving.set(false);
      }
    }
  }

  async undo(): Promise<void> {
    const change = this.undoTarget();
    if (this.busy() || !change) {
      return;
    }
    const request = this.request('write');
    this.saving.set(true);
    this.error.set('');
    try {
      await this.api.requestOnce('/api/review/revert', {
        authenticated: true,
        method: 'POST',
        signal: request.signal,
        body: {
          target_id: change.target_id,
          field: change.field,
          expected_revision: change.field_revision,
        }
      });
      if (request.signal.aborted) {
        return;
      }
      this.undoTarget.set(null);
      this.message.set('Undo recorded. It takes effect after restart.');
      await this.refresh();
    } catch (error) {
      if (!request.signal.aborted) {
        this.failed(error);
      }
    } finally {
      if (!request.signal.aborted) {
        this.saving.set(false);
      }
    }
  }

  askUndo(change: ReviewChange): void {
    this.error.set('');
    this.undoTarget.set(change);
  }

  async logout(): Promise<void> {
    if (this.busy()) {
      return;
    }
    const request = this.request('logout');
    this.loggingOut.set(true);
    try {
      await this.api.requestOnce('/api/review/logout', {
        authenticated: true,
        method: 'POST',
        signal: request.signal
      });
      if (!request.signal.aborted) {
        this.clearPrivateState();
      }
    } catch (error) {
      if (!request.signal.aborted && error instanceof ApiError && error.status === 401) {
        this.clearPrivateState();
      }
    } finally {
      this.loggingOut.set(false);
    }
  }
}
