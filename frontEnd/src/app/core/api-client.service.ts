import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, firstValueFrom, map, Observable, takeUntil, throwError } from 'rxjs';
import { environment } from '../../environments/environment';

export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiRequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  headers?: Record<string, string>;
  authenticated?: boolean;
  signal?: AbortSignal;
}

/** Shared JSON transport. Feature services own state, retries, and authentication. */
@Injectable({ providedIn: 'root' })
export class ApiClient {
  private readonly http = inject(HttpClient);

  request<T>(path: string, options: ApiRequestOptions = {}): Observable<T> {
    let headers = new HttpHeaders(options.headers);
    if (!headers.has('Accept')) {
      headers = headers.set('Accept', 'application/json');
    }
    const request = this.http.request<T>(options.method ?? 'GET', environment.apiUrl + path, {
      body: options.body,
      headers,
      observe: 'response',
      responseType: 'json',
      credentials: options.authenticated ? 'include' : 'omit',
      cache: 'no-store',
    }).pipe(
      map(response => {
        if (response.body === null) {
          throw new ApiError(response.status, 'The server returned an empty response.');
        }
        return response.body;
      }),
      catchError((error: unknown) => throwError(() => normalizeApiError(error))),
    );

    // Unsubscribing cancels HttpClient's underlying request. An abort errors the
    // Promise adapter too, so an awaiting caller never hangs after cancellation.
    return options.signal ? request.pipe(takeUntil(aborted(options.signal))) : request;
  }

  requestOnce<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    return firstValueFrom(this.request<T>(path, options));
  }
}

function aborted(signal: AbortSignal): Observable<never> {
  return new Observable(subscriber => {
    const cancel = () => subscriber.error(new DOMException('The request was cancelled.', 'AbortError'));
    if (signal.aborted) {
      cancel();
      return;
    }
    signal.addEventListener('abort', cancel, { once: true });
    return () => signal.removeEventListener('abort', cancel);
  });
}

function normalizeApiError(error: unknown): Error {
  if (!(error instanceof HttpErrorResponse)) {
    return error instanceof Error ? error : new ApiError(0, 'The request could not be completed.');
  }
  if (error.status === 0) {
    return new ApiError(0, 'The request could not be completed. Check your connection.');
  }
  if (error.status >= 200 && error.status < 300) {
    return new ApiError(error.status, 'The server returned an invalid JSON response.');
  }

  return new ApiError(
    error.status,
    responseErrorMessage(error.error, error.headers.get('Content-Type')) ?? `Request failed (${error.status}).`,
  );
}

/** Error bodies can be JSON, plain text, or an HTML page from a proxy. */
function responseErrorMessage(body: unknown, contentType: string | null): string | null {
  if (typeof body === 'string') {
    // Angular keeps non-JSON bodies as strings for unsuccessful responses.
    // HTML pages are not useful messages, even though interpolation escapes them.
    const mediaType = contentType?.split(';')[0].trim().toLowerCase();
    if (mediaType === 'text/html' || mediaType === 'application/xhtml+xml') {
      return null;
    }
    return readableMessage(body);
  }
  if (Array.isArray(body)) {
    return validationMessages(body);
  }
  if (!isRecord(body)) {
    return null;
  }

  // FastAPI detail, common message/error envelopes, and problem-details title.
  // Only explicit message fields are read; arbitrary objects are never dumped.
  for (const candidate of [body['detail'], body['message'], body['msg'], body['error'], body['title']]) {
    const message = Array.isArray(candidate)
      ? validationMessages(candidate)
      : itemMessage(candidate);
    if (message) {
      return message;
    }
  }
  return null;
}

function validationMessages(items: readonly unknown[]): string | null {
  const messages = items.map(itemMessage).filter((message): message is string => message !== null);
  return messages.length ? [...new Set(messages)].join(' ') : null;
}

function itemMessage(value: unknown): string | null {
  if (typeof value === 'string') {
    return readableMessage(value);
  }
  if (isRecord(value)) {
    return readableMessage(value['msg']) ?? readableMessage(value['message']);
  }
  return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function readableMessage(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null;
  }
  const message = value.trim();
  // Also recognize HTML when a proxy omits or mislabels Content-Type.
  return message && !/^<(?:!doctype\b|\/?(?:html|head|body|script|style|title|h[1-6]|p|div)\b)[^>]*>/i.test(message)
    ? message
    : null;
}

export function errorMessage(error: unknown): string {
  return readableMessage(error instanceof Error ? error.message : error) ?? 'The request could not be completed.';
}
