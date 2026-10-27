export const LOG_COLUMNS = [
  { id: 'time', header: 'Time', width: 85, numeric: false, defaultVisible: true },
  { id: 'ip', header: 'IP hash', width: 80, numeric: false, defaultVisible: true },
  { id: 'request', header: 'Request', width: 130, numeric: false, defaultVisible: true },
  { id: 'query', header: 'Query', width: 300, numeric: false, defaultVisible: true },
  { id: 'status', header: 'Status', width: 70, numeric: true, defaultVisible: true },
  { id: 'results', header: 'Results', width: 70, numeric: true, defaultVisible: true },
  { id: 'duration', header: 'Time (ms)', width: 70, numeric: true, defaultVisible: true },
  { id: 'client', header: 'Client', width: 140, numeric: false, defaultVisible: true },
  { id: 'filters', header: 'Filters', width: 280, numeric: false, defaultVisible: true },
  { id: 'reason', header: 'Failure reason', width: 240, numeric: false, defaultVisible: false },
  { id: 'id', header: 'Event ID', width: 95, numeric: false, defaultVisible: false },
] as const;

export type LogColumn = typeof LOG_COLUMNS[number];
export type LogColumnId = LogColumn['id'];

export interface LogSort {
  column: LogColumnId;
  direction: 'asc' | 'desc';
}

export const DEFAULT_LOG_SORT: LogSort = { column: 'time', direction: 'desc' };

export function isLogColumnId(value: string): value is LogColumnId {
  return LOG_COLUMNS.some(column => column.id === value);
}
