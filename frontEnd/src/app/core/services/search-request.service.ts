import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError, timer } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface RankedStatus {
  active: boolean;
  region: string | null;
  remainingSeconds: number;
}

@Injectable({
  providedIn: 'root',
})
export class SearchRequestService {
  constructor(private http: HttpClient) {
    this.rankedStatusSubject = new BehaviorSubject(this.getRankedStatus());
    this.rankedStatus$ = this.rankedStatusSubject.asObservable();
    timer(0, 1000)
      .pipe(map(() => this.getRankedStatus()))
      .subscribe((status) => this.rankedStatusSubject.next(status));
  }

  private readonly apiUrl = environment.apiUrl;
  private readonly searchErrorSubject = new BehaviorSubject<string | null>(
    null,
  );
  readonly searchError$ = this.searchErrorSubject.asObservable();

  private readonly rankedStatusSubject: BehaviorSubject<RankedStatus>;
  readonly rankedStatus$: Observable<RankedStatus>;

  clearSearchError(): void {
    this.searchErrorSubject.next(null);
  }

  private apiPost(path: string, body: object): Observable<any> {
    this.clearSearchError();
    return this.http
      .post(this.apiUrl + path, body, {
        headers: { 'X-Client-Id': 'AnisongDB' },
      })
      .pipe(catchError((error: HttpErrorResponse) => this.handleError(error)));
  }

  getFirstNRequest(): Observable<any> {
    return this.apiPost('/api/get_50_random_songs', {});
  }

  searchRequest(body: object): Observable<any> {
    return this.apiPost('/api/search_request', body);
  }

  seasonRequest(body: object): Observable<any> {
    return this.apiPost('/api/season_request', body);
  }

  artistIdsSearchRequest(body: object): Observable<any> {
    return this.apiPost('/api/artist_ids_request', body);
  }

  composerIdsSearchRequest(body: object): Observable<any> {
    return this.apiPost('/api/composer_ids_request', body);
  }

  annIdsSearchRequest(body: object): Observable<any> {
    return this.apiPost('/api/ann_ids_request', body);
  }

  malIdsSearchRequest(body: object): Observable<any> {
    return this.apiPost('/api/mal_ids_request', body);
  }

  annSongIdsSearchRequest(body: object): Observable<any> {
    return this.apiPost('/api/ann_song_ids_request', body);
  }

  amqSongIdsSearchRequest(body: object): Observable<any> {
    return this.apiPost('/api/amq_song_ids_request', body);
  }

  // AMQ ranked window: 20:30–21:23 local in Central, Western, or Eastern regions.
  private static readonly RANKED_START_SEC = (20 * 60 + 30) * 60;
  private static readonly RANKED_END_SEC = (21 * 60 + 23) * 60;

  // Cached Intl formatters per zone for local time-of-day in seconds.
  private static readonly RANKED_REGIONS: ReadonlyArray<{
    region: string;
    localSeconds: (date: Date) => number;
  }> = [
    { timeZone: 'Europe/Copenhagen', region: 'Central' },
    { timeZone: 'America/Chicago', region: 'Western' },
    { timeZone: 'Asia/Tokyo', region: 'Eastern' },
  ].map(({ timeZone, region }) => {
    const fmt = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hourCycle: 'h23',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    return {
      region,
      localSeconds(date: Date) {
        const parts = fmt.formatToParts(date);
        const get = (type: string) =>
          Number(parts.find((p) => p.type === type)?.value || 0);
        return get('hour') * 3600 + get('minute') * 60 + get('second');
      },
    };
  });

  private static initialRankedStatus(): RankedStatus {
    return {
      active: false,
      region: null,
      remainingSeconds: 0,
    };
  }

  // Determine whether the AMQ ranked window is currently active for any supported time zone
  getRankedStatus(date: Date = new Date()): RankedStatus {
    for (const {
      region,
      localSeconds,
    } of SearchRequestService.RANKED_REGIONS) {
      const localSec = localSeconds(date);

      if (
        localSec >= SearchRequestService.RANKED_START_SEC &&
        localSec < SearchRequestService.RANKED_END_SEC
      ) {
        return {
          active: true,
          region,
          remainingSeconds: SearchRequestService.RANKED_END_SEC - localSec,
        };
      }
    }

    return SearchRequestService.initialRankedStatus();
  }

  formatRankedRemaining(status: RankedStatus): string {
    if (!status.active) {
      return '';
    }
    const minutes = Math.floor(status.remainingSeconds / 60);
    const seconds = status.remainingSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  // Log HTTP failures, surface a message for the UI, and rethrow for subscribers.
  private handleError(error: HttpErrorResponse) {
    console.error(
      error.status === 0
        ? 'An error occurred:'
        : `Backend returned code ${error.status}, body was:`,
      error.error,
    );
    this.searchErrorSubject.next(this.formatSearchErrorMessage(error));
    return throwError(() => error);
  }

  private formatSearchErrorMessage(error: HttpErrorResponse): string {
    return this.extractErrorDetail(error) ?? 'Search failed';
  }

  private extractErrorDetail(error: HttpErrorResponse): string | null {
    const body = error.error;
    if (body == null) {
      return null;
    }

    if (typeof body === 'string') {
      const text = body.trim();
      return text || null;
    }

    if (typeof body !== 'object') {
      return null;
    }

    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === 'string') {
      const text = detail.trim();
      return text || null;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (typeof item === 'string') {
            return item.trim();
          }
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg: unknown }).msg).trim();
          }
          return '';
        })
        .filter(Boolean);
      return messages.length ? messages.join(' ') : null;
    }

    return null;
  }
}
