import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class SearchRequestService {

  constructor(private http: HttpClient) { }

  configUrl = 'assets/config.json'

  getFirstNRequest(): Observable<any> {
    return this.http.post("http://46.101.197.163:81/get_first_n_songs", { "nb_songs": 30 }).pipe(
      catchError(this.handleError)
    );;
  }

  searchRequest(body: object): Observable<any> {

    return this.http.post("http://46.101.197.163:81/search_request", body).pipe(
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