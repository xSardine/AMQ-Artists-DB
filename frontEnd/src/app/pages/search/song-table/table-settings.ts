import { StorageDefinition } from '../../../core/browser-storage.service';
import { booleanValue, objectValue, recoverValue, textValue, uniqueValues } from '../../../core/storage-validation';

export interface TableSettings {
  order: string[];
  visibility: Record<string, boolean>;
}

function columnId(value: unknown): string {
  const id = textValue(value, 100, false);
  if (!/^[a-z][a-z0-9-]*$/.test(id)) throw new Error('Invalid column id.');
  return id;
}

export const TABLE_SETTINGS: StorageDefinition<TableSettings> = {
  key: 'anisongdb-table-settings',
  defaults: () => ({ order: [], visibility: {} }),
  recover(value) {
    const record = objectValue(value);
    const order = Array.isArray(record['order']) ? record['order'] : [];
    const visibility = recoverValue(record['visibility'], objectValue, {});
    return {
      order: [...new Set(order.flatMap(id => {
        const valid = recoverValue(id, columnId, null);
        return valid === null ? [] : [valid];
      }))].slice(0, 1000),
      visibility: Object.fromEntries(Object.entries(visibility).flatMap(([id, shown]) => {
        const valid = recoverValue(id, columnId, null);
        if (valid === null || typeof shown !== 'boolean') return [];
        return [[valid, shown] as const];
      })),
    };
  },
  parse(value) {
    const record = objectValue(value, ['order', 'visibility']);
    if (!Array.isArray(record['order']) || record['order'].length > 1000) throw new Error('Invalid column order.');
    return {
      order: uniqueValues(record['order'].map(columnId)),
      visibility: Object.fromEntries(Object.entries(objectValue(record['visibility']))
        .map(([id, shown]) => [columnId(id), booleanValue(shown)])),
    };
  },
};
