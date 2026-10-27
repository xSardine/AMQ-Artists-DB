import { StorageDefinition } from '../../core/browser-storage.service';
import {
  integerValue,
  objectValue,
  optionValue,
  recoverValue,
  textValue,
  uniqueValues,
} from '../../core/storage-validation';
import { DEFAULT_LOG_SORT, LOG_COLUMNS, LogColumnId, LogSort } from './log-columns';
import { LogFilterState, LogTimeSettings } from './log-types';

export const DEFAULT_FILTERS: LogFilterState = {
  search: '',
  requestGroup: 'all',
  outcome: 'all',
};

export interface LogSettings {
  filters: LogFilterState;
  time: LogTimeSettings;
  eventLimit: number;
  columns: {
    order: LogColumnId[];
    visible: LogColumnId[];
  };
  sort: LogSort;
}

function parseEventLimit(value: unknown): number {
  const limit = integerValue(value, 1);
  if (limit > 1000) throw new Error('Log event limit must be between 1 and 1000.');
  return limit;
}

export const LOG_SETTINGS: StorageDefinition<LogSettings> = {
  key: 'anisongdb-log-settings',
  defaults: () => ({
    filters: structuredClone(DEFAULT_FILTERS),
    time: { dateFormat: 'ymd', timeFormat: 'h12', timeZone: 'local' },
    eventLimit: 100,
    columns: {
      order: LOG_COLUMNS.map(column => column.id),
      visible: LOG_COLUMNS.filter(column => column.defaultVisible).map(column => column.id),
    },
    sort: { ...DEFAULT_LOG_SORT },
  }),
  recover(value) {
    const defaults = LOG_SETTINGS.defaults();
    const record = objectValue(value);
    const filters = recoverValue(record['filters'], objectValue, {});
    const time = recoverValue(record['time'], objectValue, {});
    const columns = recoverValue(record['columns'], objectValue, {});
    const sort = recoverValue(record['sort'], objectValue, {});
    const columnIds = LOG_COLUMNS.map(column => column.id);
    const recoverColumns = (value: unknown, fallback: LogColumnId[]): LogColumnId[] => {
      if (!Array.isArray(value)) return fallback;
      return [...new Set(value.flatMap(id => {
        const valid = recoverValue(id, value => optionValue(value, columnIds), null);
        return valid === null ? [] : [valid];
      }))];
    };
    const order = recoverColumns(columns['order'], defaults.columns.order);
    return {
      filters: {
        search: recoverValue(filters['search'], value => textValue(value, 1000), defaults.filters.search),
        requestGroup: recoverValue(
          filters['requestGroup'], value => optionValue(value, ['all', 'text', 'ids', 'other']), defaults.filters.requestGroup,
        ),
        outcome: recoverValue(
          filters['outcome'], value => optionValue(value, ['all', 'completed', 'failed', 'zero-results']), defaults.filters.outcome,
        ),
      },
      time: {
        dateFormat: recoverValue(
          time['dateFormat'], value => optionValue(value, ['ymd', 'mdy', 'dmy']), defaults.time.dateFormat,
        ),
        timeFormat: recoverValue(
          time['timeFormat'], value => optionValue(value, ['h24', 'h12']), defaults.time.timeFormat,
        ),
        timeZone: recoverValue(
          time['timeZone'], value => optionValue(value, ['local', 'utc']), defaults.time.timeZone,
        ),
      },
      eventLimit: recoverValue(record['eventLimit'], parseEventLimit, defaults.eventLimit),
      columns: {
        order: [...order, ...columnIds.filter(id => !order.includes(id))],
        visible: recoverColumns(columns['visible'], defaults.columns.visible),
      },
      sort: {
        column: recoverValue(
          sort['column'], value => optionValue(value, columnIds), defaults.sort.column,
        ),
        direction: recoverValue(
          sort['direction'], value => optionValue(value, ['asc', 'desc']), defaults.sort.direction,
        ),
      },
    };
  },
  parse(value) {
    const record = objectValue(value, ['filters', 'time', 'eventLimit', 'columns', 'sort']);
    const filters = objectValue(record['filters'], ['search', 'requestGroup', 'outcome']);
    const time = objectValue(record['time'], ['dateFormat', 'timeFormat', 'timeZone']);
    const eventLimit = parseEventLimit(record['eventLimit']);
    const columns = objectValue(record['columns'], ['order', 'visible']);
    const columnIds = LOG_COLUMNS.map(column => column.id);
    const parseColumns = (value: unknown): LogColumnId[] => {
      if (!Array.isArray(value) || value.length > columnIds.length) throw new Error('Invalid log columns.');
      return uniqueValues(value.map(id => optionValue(id, columnIds)));
    };
    const order = parseColumns(columns['order']);
    if (order.length !== columnIds.length) throw new Error('Missing log columns.');
    const sort = objectValue(record['sort'], ['column', 'direction']);
    return {
      filters: {
        search: textValue(filters['search'], 1000),
        requestGroup: optionValue(filters['requestGroup'], ['all', 'text', 'ids', 'other']),
        outcome: optionValue(filters['outcome'], ['all', 'completed', 'failed', 'zero-results']),
      },
      time: {
        dateFormat: optionValue(time['dateFormat'], ['ymd', 'mdy', 'dmy']),
        timeFormat: optionValue(time['timeFormat'], ['h24', 'h12']),
        timeZone: optionValue(time['timeZone'], ['local', 'utc']),
      },
      eventLimit,
      columns: { order, visible: parseColumns(columns['visible']) },
      sort: {
        column: optionValue(sort['column'], columnIds),
        direction: optionValue(sort['direction'], ['asc', 'desc']),
      },
    };
  },
};
