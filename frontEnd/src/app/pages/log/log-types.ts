export interface LogEvent {
  id: string;
  ts: string;
  endpoint: string;
  http_status?: number | null;
  reason?: string;
  errors?: unknown;
  ip?: string;
  client?: string;
  body?: unknown;
  duration_ms?: number;
  result?: {
    count: number;
  };
}

export interface LogFeed {
  events: LogEvent[];
  latest_id: string | null;
  stream_id: string;
}

export type RequestGroup = 'text' | 'ids' | 'other';

export interface LogFilterState {
  search: string;
  requestGroup: 'all' | RequestGroup;
  outcome: 'all' | 'completed' | 'failed' | 'zero-results';
}

export interface LogTimeSettings {
  dateFormat: 'ymd' | 'mdy' | 'dmy';
  timeFormat: 'h24' | 'h12';
  timeZone: 'local' | 'utc';
}
