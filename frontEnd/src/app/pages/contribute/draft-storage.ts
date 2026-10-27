import { StorageDefinition } from '../../core/browser-storage.service';
import {
  integerValue,
  objectValue,
  optionValue,
  recoverValue,
  textValue,
  uniqueValues,
} from '../../core/storage-validation';
import {
  allowedOperations,
  defaultOperation,
  type ContributionField,
  FIELD_DEFINITIONS,
  normalizeValue,
} from '../../shared/contributions/contribution-fields';
import type {
  ContributionOperation,
  ProposedChange,
  TargetKind,
} from '../../shared/contributions/contribution-types';

export interface DraftItem extends ProposedChange {
  client_id: string;
}

export interface DraftEditor {
  targetId: string | null;
  editingId: string | null;
  kind: TargetKind;
  search: string;
  field: ContributionField;
  operation: ContributionOperation;
  value: string | number | null;
  oldValue: string;
}

export interface SavedDraft {
  name: string;
  comment: string;
  cart: DraftItem[];
  requestId: string;
  editor: DraftEditor;
}

export const MAX_DRAFT_CHANGES = 100;

const DEFAULT_FIELDS: Record<TargetKind, ContributionField> = {
  anime: 'anime_original_title',
  artist: 'artist_original_alias',
  song: 'song_original_title',
};

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function uuid(value: unknown): string {
  const id = textValue(value, 36, false);
  if (!UUID.test(id)) throw new Error('Invalid draft identifier.');
  return id;
}

export function emptyEditor(kind: TargetKind = 'anime', search = ''): DraftEditor {
  return {
    targetId: null,
    editingId: null,
    kind,
    search,
    field: DEFAULT_FIELDS[kind],
    operation: defaultOperation(DEFAULT_FIELDS[kind]),
    value: '',
    oldValue: '',
  };
}

export function hasEditorChanges(editor: DraftEditor): boolean {
  return editor.editingId !== null
    || (editor.value !== '' && editor.value !== null)
    || editor.oldValue !== ''
    || (editor.targetId !== null && editor.operation === 'clear');
}

function editorValue(value: unknown): DraftEditor {
  const editor = objectValue(value, ['targetId', 'editingId', 'kind', 'search', 'field', 'operation', 'value', 'oldValue']);
  const field = optionValue(editor['field'], Object.keys(FIELD_DEFINITIONS) as ContributionField[]);
  const proposed = editor['value'];
  if (proposed !== null && typeof proposed !== 'string' && typeof proposed !== 'number') throw new Error('Invalid editor value.');
  if (typeof proposed === 'number' && !Number.isFinite(proposed)) throw new Error('Invalid editor number.');
  return {
    targetId: editor['targetId'] === null ? null : uuid(editor['targetId']),
    editingId: editor['editingId'] === null ? null : uuid(editor['editingId']),
    kind: optionValue(editor['kind'], ['anime', 'artist', 'song']),
    search: textValue(editor['search'], 200),
    field,
    operation: optionValue(editor['operation'], allowedOperations(field)),
    value: typeof proposed === 'string' ? textValue(proposed, 500) : proposed,
    oldValue: textValue(editor['oldValue'], 500),
  };
}

function draftItem(value: unknown): DraftItem {
  const item = objectValue(value, ['client_id', 'target_id', 'field', 'operation', 'payload', 'base_revision', 'label']);
  const field = optionValue(item['field'], Object.keys(FIELD_DEFINITIONS) as ContributionField[]);
  const operation = optionValue(item['operation'], allowedOperations(field));
  const payload = objectValue(item['payload'], ['value', 'old_value']);
  const proposed = operation === 'clear' ? null : normalizeValue(field, payload['value']);
  if (proposed !== payload['value']) throw new Error('Invalid saved contribution value.');
  if (operation === 'clear' && payload['value'] !== null) throw new Error('Invalid clear action.');
  const old = operation === 'replace_alias' ? textValue(payload['old_value'], 500, false) : null;
  if (old !== null && normalizeValue(field, old) !== old) throw new Error('Invalid saved replaced alias.');
  if (operation !== 'replace_alias' && payload['old_value'] !== null) throw new Error('Unexpected replaced alias.');
  return {
    client_id: uuid(item['client_id']),
    target_id: uuid(item['target_id']),
    field,
    operation,
    payload: { value: proposed, old_value: old },
    base_revision: integerValue(item['base_revision']),
    label: textValue(item['label'], 2000, false),
  };
}

function validateEditor(editor: DraftEditor, cart: DraftItem[]): DraftEditor {
  const edited = cart.find(item => item.client_id === editor.editingId);
  if (editor.editingId && (!edited || edited.target_id !== editor.targetId)) {
    throw new Error('Missing or mismatched edited change.');
  }
  if (editor.targetId !== null) {
    if (FIELD_DEFINITIONS[editor.field].kind !== editor.kind) throw new Error('Invalid editor field.');
  }
  return editor;
}

export function changePayload({ target_id, field, operation, payload, base_revision }: DraftItem) {
  return { target_id, field, operation, payload, base_revision };
}

export function submissionPayload(draft: SavedDraft) {
  return {
    contributor_name: draft.name.trim(),
    comment: draft.comment,
    changes: draft.cart.map(changePayload),
  };
}

export const DRAFT_STORAGE: StorageDefinition<SavedDraft> = {
  key: 'anisongdb-contribution-draft',
  syncAcrossTabs: false,
  defaults: () => ({
    name: '',
    comment: '',
    cart: [],
    requestId: crypto.randomUUID(),
    editor: emptyEditor(),
  }),
  recover(value) {
    const draft = objectValue(value);
    const savedCart = Array.isArray(draft['cart']) ? draft['cart'] : [];
    const seen = new Set<string>();
    const cart = savedCart.flatMap(value => {
      const item = recoverValue(value, draftItem, null);
      if (!item || seen.has(item.client_id)) return [];
      seen.add(item.client_id);
      return [item];
    }).slice(0, MAX_DRAFT_CHANGES);
    return {
      name: recoverValue(draft['name'], value => textValue(value, 100), ''),
      comment: recoverValue(draft['comment'], value => textValue(value, 3000), ''),
      cart,
      // A repaired submission must not reuse an ID for a potentially different payload.
      requestId: crypto.randomUUID(),
      editor: recoverValue(draft['editor'], value => validateEditor(editorValue(value), cart), emptyEditor()),
    };
  },
  parse(value) {
    const draft = objectValue(value, ['name', 'comment', 'cart', 'requestId', 'editor']);
    if (!Array.isArray(draft['cart']) || draft['cart'].length > MAX_DRAFT_CHANGES) throw new Error('Invalid submission changes.');
    const cart = draft['cart'].map(draftItem);
    uniqueValues(cart.map(item => item.client_id));
    const editor = validateEditor(editorValue(draft['editor']), cart);
    return {
      name: textValue(draft['name'], 100),
      comment: textValue(draft['comment'], 3000),
      cart,
      requestId: uuid(draft['requestId']),
      editor,
    };
  },
};
