import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class SearchRequestService {

  constructor(private http: HttpClient) { }

  configUrl = 'assets/config.json'

  /*
  http://127.0.0.1:8000
  https://anisongdb.com
  */
  api_url = "http://127.0.0.1:8000"

  getFirstNRequest(): Observable<any> {
    return this.http.post(this.api_url + "/api/get_50_random_songs", {}).pipe(
      catchError(this.handleError)
    );;
  }

  searchRequest(body: object): Observable<any> {

    return this.http.post(this.api_url + "/api/search_request", body).pipe(
      catchError(this.handleError)
    );;

  }

  artistIdsSearchRequest(body: object): Observable<any> {

    return this.http.post(this.api_url + "/api/artist_ids_request", body).pipe(
      catchError(this.handleError)
    );;

  }

  composerIdsSearchRequest(body: object): Observable<any> {

    return this.http.post(this.api_url + "/api/composer_ids_request", body).pipe(
      catchError(this.handleError)
    );;

  }

  annIdSearchRequest(body: object): Observable<any> {

    return this.http.post(this.api_url + "/api/annId_request", body).pipe(
      catchError(this.handleError)
    );;

  }

  private handleError(error: HttpErrorResponse) {
    if (error.status === 0) {
      // A client-side or network error occurred. Handle it accordingly.
      console.error('An error occurred:', error.error);
    } else {
      // The backend returned an unsuccessful response code.
      // The response body may contain clues as to what went wrong.
      console.error(
        `Backend returned code ${error.status}, body was: `, error.error);
    }
    // Return an observable with a user-facing error message.
    return throwError(
      'Something bad happened; please try again later.');
  }

}
