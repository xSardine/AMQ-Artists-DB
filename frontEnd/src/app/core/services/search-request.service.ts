import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class SearchRequestService {
  constructor(private http: HttpClient) {}

  configUrl = 'assets/config.json';

  /*
  http://127.0.0.1:8000
  https://anisongdb.com
  */
  api_url = 'http://127.0.0.1:8000';

  getFirstNRequest(): Observable<any> {
    return this.http
      .post(this.api_url + '/api/get_50_random_songs', {})
      .pipe(catchError(this.handleError));
  }

  searchRequest(body: object): Observable<any> {
    return this.http
      .post(this.api_url + '/api/search_request', body)
      .pipe(catchError(this.handleError));
  }

  artistIdsSearchRequest(body: object): Observable<any> {
    return this.http
      .post(this.api_url + '/api/artist_ids_request', body)
      .pipe(catchError(this.handleError));
  }

  composerIdsSearchRequest(body: object): Observable<any> {
    return this.http
      .post(this.api_url + '/api/composer_ids_request', body)
      .pipe(catchError(this.handleError));
  }

  annIdSearchRequest(body: object): Observable<any> {
    return this.http
      .post(this.api_url + '/api/ann_ids_request', body)
      .pipe(catchError(this.handleError));
  }

  // All time zones where the ranked window is observed.
  private static readonly RANKED_TIMEZONES = [
    'Europe/Copenhagen',
    'America/Chicago',
    'Asia/Tokyo',
  ];

  // Ranked window boundaries in seconds-since-midnight.
  private static readonly RANKED_START_SEC = 73800; // 20:30:00
  private static readonly RANKED_END_SEC = 76980; // 21:23:00

  // Format `date` for `timeZone` and return how many seconds have elapsed since midnight.
  private getSecondsSinceStartOfDay(date: Date, timeZone: string): number {
    const fmt = new Intl.DateTimeFormat('en-US', {
      timeZone: timeZone,
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    const parts = fmt.formatToParts(date);
    const get = (type: string) => Number(parts.find((p) => p.type === type)?.value || 0);
    return get('hour') * 3600 + get('minute') * 60 + get('second');
  }

  // Determine whether the current time falls inside the ranked window for any tracked zone.
  // If so, return how many whole minutes remain until the window closes.
  getRankedStatusNow(): { active: boolean; remainingMinutes: number } {
    const nowDate = new Date();

    for (const tz of SearchRequestService.RANKED_TIMEZONES) {
      const localSec = this.getSecondsSinceStartOfDay(nowDate, tz);

      if (localSec >= SearchRequestService.RANKED_START_SEC && localSec < SearchRequestService.RANKED_END_SEC) {
        const remainingMinutes = Math.ceil((SearchRequestService.RANKED_END_SEC - localSec) / 60);
        return { active: true, remainingMinutes };
      }
    }

    return { active: false, remainingMinutes: 0 };
  }

  private handleError(error: HttpErrorResponse) {
    if (error.status === 0) {
      // A client-side or network error occurred. Handle it accordingly.
      console.error('An error occurred:', error.error);
    } else {
      // The backend returned an unsuccessful response code.
      // The response body may contain clues as to what went wrong.
      console.error(
        `Backend returned code ${error.status}, body was: `,
        error.error
      );
    }
    // Return an observable with a user-facing error message.
    return throwError('Something bad happened; please try again later.');
  }
}
