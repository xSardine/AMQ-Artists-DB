import { computed, DestroyRef, effect, inject, Injectable, signal, untracked } from '@angular/core';
import { ApiClient, errorMessage } from '../../core/api-client.service';
import {
  allowedOperations,
  defaultOperation,
  type ContributionField,
  FIELD_DEFINITIONS,
  normalizeValue,
} from '../../shared/contributions/contribution-fields';
import type {
  ContributionTarget,
  ContributionOperation,
} from '../../shared/contributions/contribution-types';
import { ContributionDraft } from './contribution-draft';
import { DraftEditor, emptyEditor, submissionPayload } from './draft-storage';

@Injectable()
export class ContributeState {
  private readonly api = inject(ApiClient);
  readonly draft = inject(ContributionDraft);
  readonly results = signal<ContributionTarget[]>([]);
  readonly selected = signal<ContributionTarget | null>(null);
  readonly error = signal('');
  readonly submitError = signal('');
  readonly searching = signal(false);
  readonly submitting = signal(false);
  readonly receipt = signal<number | null>(null);

  private readonly abort = new AbortController();
  private searchAbort = new AbortController();
  private targetRequestId: string | null = null;

  get kind(): DraftEditor['kind'] {
    return this.draft.editor().kind;
  }
  set kind(kind: DraftEditor['kind']) {
    if (kind === this.kind) return;
    if (!this.canReplaceEditor()) return;
    this.stopLookup();
    this.selected.set(null);
    this.results.set([]);
    this.draft.updateEditor(emptyEditor(kind, this.search));
  }

  get search(): DraftEditor['search'] {
    return this.draft.editor().search;
  }
  set search(search: DraftEditor['search']) {
    this.draft.updateEditor({ search });
  }

  get field(): DraftEditor['field'] {
    return this.draft.editor().field;
  }
  set field(field: DraftEditor['field']) {
    if (field === this.field) return;
    this.draft.updateEditor({ field, operation: defaultOperation(field), value: '', oldValue: '' });
  }

  get operation(): DraftEditor['operation'] {
    return this.draft.editor().operation;
  }
  set operation(operation: DraftEditor['operation']) {
    if (operation === this.operation) return;
    this.draft.updateEditor({ operation, value: '', oldValue: '' });
  }

  get value(): DraftEditor['value'] {
    return this.draft.editor().value;
  }
  set value(value: DraftEditor['value']) {
    this.draft.updateEditor({ value });
  }

  get oldValue(): DraftEditor['oldValue'] {
    return this.draft.editor().oldValue;
  }
  set oldValue(oldValue: DraftEditor['oldValue']) {
    this.draft.updateEditor({ oldValue });
  }

  constructor() {
    // Keystrokes update the saved editor too; only a target change needs a lookup.
    const editorTargetId = computed(() => this.draft.editor().targetId);
    effect(() => {
      const targetId = editorTargetId();
      untracked(() => {
        if (targetId === null) {
          if (this.targetRequestId !== null) this.stopLookup();
          this.selected.set(null);
        } else if (this.selected()?.id !== targetId) {
          void this.restoreTarget(targetId);
        }
      });
    });
    inject(DestroyRef).onDestroy(() => {
      this.abort.abort();
      this.searchAbort.abort();
    });
  }

  fields(): ContributionField[] {
    return Object.keys(this.selected()?.values || {}) as ContributionField[];
  }

  aliases(): string[] {
    const value = this.selected()?.values[this.field];
    return Array.isArray(value) ? value : [];
  }

  operations(): readonly ContributionOperation[] {
    return allowedOperations(this.field);
  }

  choose(target: ContributionTarget): void {
    if (this.submitting() || !this.canReplaceEditor()) return;
    const field = Object.keys(target.values)[0] as ContributionField | undefined;
    if (!field) {
      this.error.set('This record has no editable fields.');
      return;
    }
    this.stopLookup();
    this.error.set('');
    this.selected.set(target);
    this.results.set([]);
    this.draft.updateEditor({
      ...emptyEditor(target.kind, this.search),
      targetId: target.id,
      field,
      operation: defaultOperation(field),
    });
  }

  async find(): Promise<void> {
    if (this.submitting() || !this.search.trim()) return;
    if (!this.canReplaceEditor()) return;
    const request = this.beginLookup();
    this.selected.set(null);
    this.results.set([]);
    this.draft.updateEditor(emptyEditor(this.kind, this.search));
    try {
      const query = new URLSearchParams({ kind: this.kind, search: this.search.trim() });
      const targets = await this.api.requestOnce<ContributionTarget[]>(
        `/api/contribution-targets?${query}`, { signal: request.signal },
      );
      if (!request.signal.aborted) this.results.set(targets);
    } catch (error) {
      if (!request.signal.aborted) this.error.set(errorMessage(error));
    } finally {
      if (!request.signal.aborted) this.searching.set(false);
    }
  }

  add(): void {
    const target = this.selected();
    if (this.submitting() || this.searching() || !target
      || target.id !== this.draft.editor().targetId) return;
    try {
      if (!Object.hasOwn(target.values, this.field) || !this.operations().includes(this.operation)) {
        throw new Error('Select a field and action supported by this record.');
      }
      const value = this.operation === 'clear' ? null : normalizeValue(this.field, this.value);
      const oldValue = this.operation === 'replace_alias' ? this.oldValue.trim() : null;
      if (this.operation === 'replace_alias') {
        normalizeValue(this.field, oldValue);
      }
      if (this.operation === 'remove_alias' || this.operation === 'replace_alias') {
        const removed = this.operation === 'replace_alias' ? oldValue : value;
        if (!this.aliases().some(alias => alias.normalize('NFC') === String(removed).normalize('NFC'))) {
          throw new Error('That alias is no longer present. Select a current alias.');
        }
      }
      this.draft.commit({
        target_id: target.id,
        field: this.field,
        operation: this.operation,
        payload: { value, old_value: oldValue },
        base_revision: target.versions[this.field] ?? 0,
        label: target.label,
      });
      this.error.set('');
    } catch (error) {
      this.error.set(errorMessage(error));
    }
  }

  edit(clientId: string): void {
    if (this.submitting()) return;
    const item = this.draft.cart().find(item => item.client_id === clientId);
    if (!item) return;
    if (!this.canReplaceEditor()) return;
    this.stopLookup();
    this.selected.set(null);
    this.results.set([]);
    this.draft.updateEditor({
      ...emptyEditor(FIELD_DEFINITIONS[item.field].kind),
      targetId: item.target_id,
      editingId: item.client_id,
      field: item.field,
      operation: item.operation,
      value: item.payload.value,
      oldValue: item.payload.old_value ?? '',
    });
    void this.restoreTarget(item.target_id);
  }

  cancelEdit(): void {
    if (this.submitting()) return;
    this.draft.updateEditor({
      editingId: null,
      operation: defaultOperation(this.field),
      value: '',
      oldValue: '',
    });
    this.error.set('');
  }

  remove(clientId: string): void {
    if (this.submitting()) return;
    if (this.draft.editingId() === clientId) {
      this.stopLookup();
      this.selected.set(null);
    }
    this.draft.remove(clientId);
  }

  discardDraft(): void {
    if (this.submitting()) return;
    this.stopLookup();
    this.selected.set(null);
    this.results.set([]);
    this.error.set('');
    this.submitError.set('');
    this.draft.clear();
  }

  retryTarget(): void {
    const targetId = this.draft.editor().targetId;
    if (!this.submitting() && !this.searching() && targetId) {
      void this.restoreTarget(targetId);
    }
  }

  private canReplaceEditor(): boolean {
    if (!this.draft.hasUnfinishedChange()) return true;
    this.error.set('Add, save, or cancel the current change before selecting another record or change.');
    return false;
  }

  private beginLookup(): AbortController {
    this.searchAbort.abort();
    this.targetRequestId = null;
    const request = this.searchAbort = new AbortController();
    this.searching.set(true);
    this.error.set('');
    return request;
  }

  private stopLookup(): void {
    this.searchAbort.abort();
    this.targetRequestId = null;
    this.searching.set(false);
  }

  private async restoreTarget(targetId: string): Promise<void> {
    if (this.targetRequestId === targetId && !this.searchAbort.signal.aborted) return;
    const request = this.beginLookup();
    this.targetRequestId = targetId;
    try {
      const target = await this.api.requestOnce<ContributionTarget>(
        '/api/contribution-targets/' + targetId, { signal: request.signal },
      );
      if (request.signal.aborted || this.draft.editor().targetId !== targetId) return;
      if (target.kind !== this.kind || !Object.hasOwn(target.values, this.field)) {
        throw new Error('This record no longer supports the drafted field. Select it again.');
      }
      this.selected.set(target);
    } catch (error) {
      if (!request.signal.aborted) this.error.set(errorMessage(error));
    } finally {
      if (!request.signal.aborted) {
        this.targetRequestId = null;
        this.searching.set(false);
      }
    }
  }

  async submit(): Promise<void> {
    if (this.submitting() || !this.draft.name.trim() || !this.draft.cart().length) return;
    if (this.searching() || this.draft.hasUnfinishedChange()) {
      this.error.set('Finish or cancel the current change before submitting.');
      return;
    }
    if (/[\u0000-\u001f]/.test(this.draft.name)) {
      this.submitError.set('Enter a single-line contributor name.');
      return;
    }
    const submitted = this.draft.snapshot();
    const body = { ...submissionPayload(submitted), client_request_id: submitted.requestId };
    this.submitting.set(true);
    this.submitError.set('');
    try {
      await this.draft.saved.settled();
      if (this.abort.signal.aborted) return;
      const response = await this.api.requestOnce<{ submission_id: number }>('/api/contributions', {
        method: 'POST',
        signal: this.abort.signal,
        body,
      });
      if (this.abort.signal.aborted) return;
      this.draft.completeSubmission(submitted);
      this.results.set([]);
      this.receipt.set(response.submission_id);
    } catch (error) {
      if (!this.abort.signal.aborted) this.submitError.set(errorMessage(error));
    } finally {
      this.submitting.set(false);
    }
  }
}
