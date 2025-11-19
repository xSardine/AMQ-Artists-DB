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

  // Returns current ranked status and minutes left using IANA zones
  getRankedStatusNow(): { active: boolean; remainingMinutes: number } {
    const nowDate = new Date();
    const zones = [
      'America/Chicago',
      'Asia/Tokyo',
      'Europe/Copenhagen',
    ];

    const START_SEC = 73800; // 20:30:00
    const END_SEC = 76980;   // 21:23:00

    for (const tz of zones) {
      const fmt = new Intl.DateTimeFormat('en-US', {
        timeZone: tz,
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
      const parts = fmt.formatToParts(nowDate);
      const get = (t: string) => Number(parts.find(p => p.type === t)?.value || 0);
      const hh = get('hour');
      const mm = get('minute');
      const ss = get('second');
      const localSec = hh * 3600 + mm * 60 + ss;

      if (localSec >= START_SEC && localSec < END_SEC) {
        const remainingMs = (END_SEC - localSec) * 1000;
        const remainingMinutes = Math.ceil(remainingMs / 60000);
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
