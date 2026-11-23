import { computed, DestroyRef, effect, inject, Injectable, signal, untracked } from '@angular/core';
import { Subject } from 'rxjs';
import { BrowserStorage } from '../../core/browser-storage.service';
import { ApiClient, ApiError, errorMessage } from '../../core/api-client.service';
import { AccessSession } from '../../core/access-session';
import { DEFAULT_FILTERS, LOG_SETTINGS } from './log-settings';
import { LogEvent, LogFeed, LogFilterState, LogTimeSettings } from './log-types';
import { createLogTimeFormatter, describeLogEvent, eventSearchBlob, finiteNumber, requestGroupForEndpoint } from './log-presenter';
import { getRankedStatus } from '../../shared/utils/ranked-schedule';

@Injectable()
export class LogState {
  private readonly api = inject(ApiClient);
  readonly saved = inject(BrowserStorage).record(LOG_SETTINGS);
  readonly authenticated = signal(false);
  readonly polling = signal(true);
  readonly autoScroll = signal(true);
  readonly events = signal<LogEvent[]>([]);
  readonly filters = computed(() => this.saved.value().filters);
  readonly timeSettings = computed(() => this.saved.value().time);
  readonly formatTime = computed(() => createLogTimeFormatter(this.timeSettings(), false));
  readonly eventLimit = computed(() => this.saved.value().eventLimit);
  readonly feedError = signal('');
  readonly loggingOut = signal(false);
  readonly clock = signal(new Date());
  readonly beforeUpdate = new Subject<void>();
  private readonly records = computed(() => this.events().map(event => {
    const description = describeLogEvent(event);
    return { event, description, search: eventSearchBlob(event, description) };
  }));
  readonly filtered = computed(() => {
    const filters = this.filters();
    const search = filters.search.trim().toLowerCase();
    return this.records().filter(record => {
      const event = record.event;
      if (filters.requestGroup !== 'all' && filters.requestGroup !== requestGroupForEndpoint(event.endpoint)) return false;
      const status = finiteNumber(event.http_status);
      switch (filters.outcome) {
        case 'completed':
          if (status === null || status >= 400) return false;
          break;
        case 'failed':
          if (status === null || status < 400) return false;
          break;
        case 'zero-results':
          if (status === null || status >= 400 || finiteNumber(event.result?.count) !== 0) return false;
          break;
      }
      return !search || record.search.includes(search);
    });
  });
  readonly status = computed(() => {
    if (this.feedError()) return 'Error: ' + this.feedError();
    const shown = this.filtered().length;
    const total = this.events().length;
    const timestamp = this.formatTime()(this.clock().toISOString());
    return `${shown} shown · ${total}/${this.eventLimit()} events · ${timestamp}`;
  });
  readonly ranked = computed(() => getRankedStatus(this.clock()).region);

  private readonly lifetime = new AbortController();
  private feedRequest: AbortController | null = null;
  private timer: number | null = null;
  private cursor: string | null = null;
  private streamId: string | null = null;
  private clearedThrough: string | null = null;
  private activeLimit = this.eventLimit();
  private sessionGeneration = 0;

  constructor() {
    const generation = this.sessionGeneration;
    void this.api.requestOnce<AccessSession>('/api/log/session', {
      authenticated: true,
      signal: this.lifetime.signal,
    }).then(session => {
      if (!this.lifetime.signal.aborted && generation === this.sessionGeneration && session.authenticated) {
        this.onLogin(session);
      }
    }).catch(() => {});

    effect(() => {
      const authenticated = this.authenticated();
      const polling = this.polling();
      const limit = this.eventLimit();
      untracked(() => {
        this.stopFeed();
        const limitChanged = limit !== this.activeLimit;
        this.activeLimit = limit;
        if (limitChanged) {
          this.cursor = null;
          this.replaceEvents(this.events().slice(-limit));
        }
        // Changing the window is an explicit refresh even when polling is paused.
        if (authenticated && (polling || limitChanged)) void this.fetch(limitChanged);
      });
    });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) this.stopFeed();
      else if (this.authenticated() && this.polling()) void this.fetch();
    }, { signal: this.lifetime.signal });

    inject(DestroyRef).onDestroy(() => {
      this.lifetime.abort();
      this.stopFeed();
      this.beforeUpdate.complete();
    });
  }

  onLogin(session: AccessSession): void {
    this.stopFeed();
    this.sessionGeneration++;
    this.cursor = null;
    this.streamId = null;
    this.clearedThrough = null;
    this.replaceEvents([]);
    this.feedError.set('');
    this.polling.set(true);
    this.autoScroll.set(true);
    this.authenticated.set(session.authenticated);
  }

  updateFilters(change: Partial<LogFilterState>): void {
    this.saved.update(current => ({ ...current, filters: { ...current.filters, ...change } }));
  }

  resetFilters(): void {
    this.updateFilters(structuredClone(DEFAULT_FILTERS));
  }

  setTimeSetting<K extends keyof LogTimeSettings>(name: K, value: LogTimeSettings[K]): void {
    this.saved.update(current => ({ ...current, time: { ...current.time, [name]: value } }));
  }

  setEventLimit(eventLimit: number): void {
    this.saved.update(current => ({ ...current, eventLimit }));
  }

  clear(): void {
    this.stopFeed();
    this.clearedThrough = this.cursor ?? this.events().at(-1)?.id ?? this.clearedThrough;
    this.replaceEvents([]);
    if (this.polling()) void this.fetch();
  }

  private replaceEvents(events: LogEvent[]): void {
    this.beforeUpdate.next();
    this.events.set(events);
  }

  private stopFeed(): void {
    if (this.timer !== null) window.clearTimeout(this.timer);
    this.timer = null;
    this.feedRequest?.abort();
    this.feedRequest = null;
  }

  private async fetch(explicitRefresh = false): Promise<void> {
    if (!this.authenticated() || (!this.polling() && !explicitRefresh)
      || document.hidden || this.feedRequest) return;
    if (this.timer !== null) window.clearTimeout(this.timer);
    this.timer = null;
    const request = new AbortController();
    this.feedRequest = request;
    const since = this.cursor ?? this.clearedThrough;
    let restartSnapshot = false;
    try {
      const query = new URLSearchParams({ limit: String(this.eventLimit()) });
      if (since !== null) query.set('since', since);
      const data = await this.api.requestOnce<LogFeed>('/api/log/feed?' + query, {
        authenticated: true,
        signal: request.signal,
      });
      if (request.signal.aborted || !this.authenticated()) return;
      if (!data || !Array.isArray(data.events) || typeof data.stream_id !== 'string'
        || (data.latest_id !== null && typeof data.latest_id !== 'string')) {
        throw new Error('Invalid log feed response.');
      }

      // A restarted server has a new counter. An old cursor would otherwise
      // hide its events until the new counter caught up with the old one.
      if (this.streamId !== null && this.streamId !== data.stream_id) {
        this.streamId = data.stream_id;
        this.cursor = null;
        this.clearedThrough = null;
        this.replaceEvents([]);
        restartSnapshot = since !== null;
      }
      if (restartSnapshot) return;

      const replace = this.cursor === null;
      this.streamId = data.stream_id;
      const existing = replace ? [] : this.events();
      const ids = new Set(existing.map(event => event.id));
      const incoming = data.events.filter(event => {
        if (ids.has(event.id)) return false;
        ids.add(event.id);
        return true;
      });
      if (replace || incoming.length) {
        this.replaceEvents([...existing, ...incoming].slice(-this.eventLimit()));
      }
      this.cursor = data.latest_id ?? this.cursor;
      this.feedError.set('');
      this.clock.set(new Date());
    } catch (error) {
      if (request.signal.aborted) return;
      if (error instanceof ApiError && error.status === 401) {
        this.sessionGeneration++;
        this.authenticated.set(false);
        this.replaceEvents([]);
      } else {
        this.feedError.set(errorMessage(error));
        this.clock.set(new Date());
      }
    } finally {
      if (this.feedRequest === request) {
        this.feedRequest = null;
        if (this.authenticated() && !document.hidden) {
          if (restartSnapshot) void this.fetch(true);
          else if (this.polling()) this.timer = window.setTimeout(() => void this.fetch(), 1000);
        }
      }
    }
  }

  async logout(): Promise<void> {
    if (this.loggingOut()) return;
    this.loggingOut.set(true);
    try {
      await this.api.requestOnce('/api/log/logout', {
        authenticated: true,
        method: 'POST',
        signal: this.lifetime.signal,
      });
      if (this.lifetime.signal.aborted) return;
      this.sessionGeneration++;
      this.authenticated.set(false);
      this.stopFeed();
      this.replaceEvents([]);
    } catch {
      // Leave the session active so logout can be retried.
    } finally {
      if (!this.lifetime.signal.aborted) this.loggingOut.set(false);
    }
  }
}
