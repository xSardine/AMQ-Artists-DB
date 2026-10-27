import { computed, inject, Injectable } from '@angular/core';
import { defaultOperation } from '../../shared/contributions/contribution-fields';
import { BrowserStorage } from '../../core/browser-storage.service';
import {
  DRAFT_STORAGE,
  MAX_DRAFT_CHANGES,
  DraftEditor,
  DraftItem,
  SavedDraft,
  emptyEditor,
  changePayload,
  hasEditorChanges,
  submissionPayload,
} from './draft-storage';

@Injectable()
export class ContributionDraft {
  readonly saved = inject(BrowserStorage).record(DRAFT_STORAGE);
  readonly cart = computed(() => this.saved.value().cart);
  readonly editor = computed(() => this.saved.value().editor);
  readonly editingId = computed(() => this.editor().editingId);
  readonly full = computed(() => this.cart().length >= MAX_DRAFT_CHANGES);
  readonly hasUnfinishedChange = computed(() => hasEditorChanges(this.editor()));
  readonly hasContent = computed(() => this.cart().length > 0
    || this.comment !== ''
    || this.hasUnfinishedChange());

  get name(): string {
    return this.saved.value().name;
  }
  set name(name: string) {
    this.change(current => ({ ...current, name }));
  }

  get comment(): string {
    return this.saved.value().comment;
  }
  set comment(comment: string) {
    this.change(current => ({ ...current, comment }));
  }

  snapshot(): SavedDraft {
    return this.saved.value();
  }

  updateEditor(change: Partial<DraftEditor>): void {
    const unchanged = Object.entries(change).every(([key, value]) =>
      this.editor()[key as keyof DraftEditor] === value
    );
    if (unchanged) return;
    this.saved.update(current => ({ ...current, editor: { ...current.editor, ...change } }));
  }

  commit(item: Omit<DraftItem, 'client_id'>): void {
    const editingId = this.editingId();
    if (editingId && !this.cart().some(item => item.client_id === editingId)) {
      throw new Error('This change is no longer in your draft.');
    }
    if (!editingId && this.full()) {
      throw new Error(`A submission can contain up to ${MAX_DRAFT_CHANGES} changes.`);
    }
    const duplicate = this.cart().some(current => current.client_id !== editingId
      && current.target_id === item.target_id
      && current.field === item.field
      && current.operation === item.operation
      && String(current.payload.value).normalize('NFC') === String(item.payload.value).normalize('NFC')
      && current.payload.old_value?.normalize('NFC') === item.payload.old_value?.normalize('NFC'));
    if (duplicate) throw new Error('This exact change is already in your submission.');
    const entry = { ...item, client_id: editingId || crypto.randomUUID() };
    this.change(current => ({
      ...current,
      cart: editingId
        ? current.cart.map(item => item.client_id === editingId ? entry : item)
        : [...current.cart, entry],
      editor: {
        ...current.editor,
        editingId: null,
        operation: defaultOperation(current.editor.field),
        value: '',
        oldValue: '',
      },
    }));
  }

  remove(clientId: string): void {
    if (!this.cart().some(item => item.client_id === clientId)) return;
    this.change(current => ({
      ...current,
      cart: current.cart.filter(entry => entry.client_id !== clientId),
      editor: current.editor.editingId === clientId
        ? emptyEditor(current.editor.kind, current.editor.search) : current.editor,
    }));
  }

  clear(): void {
    this.change(current => ({ ...current, cart: [], comment: '', editor: emptyEditor() }));
  }

  completeSubmission(submitted: SavedDraft): void {
    // A storage conflict can be resolved while a request is in flight. Only
    // remove unchanged entries from the snapshot the server actually received.
    const sent = new Map(submitted.cart.map(item => [item.client_id, JSON.stringify(changePayload(item))]));
    this.change(current => {
      const cart = current.cart.filter(item => sent.get(item.client_id) !== JSON.stringify(changePayload(item)));
      const editorChanged = JSON.stringify(current.editor) !== JSON.stringify(submitted.editor);
      const editor = editorChanged ? { ...current.editor } : emptyEditor();
      if (editor.editingId && !cart.some(item => item.client_id === editor.editingId)) {
        editor.editingId = null;
      }
      return {
        ...current,
        cart,
        comment: current.comment === submitted.comment ? '' : current.comment,
        editor,
      };
    });
  }

  private change(update: (current: SavedDraft) => SavedDraft): void {
    this.saved.update(current => {
      const next = update(current);
      if (JSON.stringify(submissionPayload(current)) !== JSON.stringify(submissionPayload(next))) {
        next.requestId = crypto.randomUUID();
      }
      return next;
    });
  }
}
