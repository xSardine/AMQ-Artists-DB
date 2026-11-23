import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { ApiClient, errorMessage } from './api-client.service';
import { AccessSession } from './access-session';

/** Provided by each login form so its request state and lifetime stay independent. */
@Injectable()
export class LoginRequest {
  private readonly api = inject(ApiClient);
  private readonly abort = new AbortController();
  private readonly requestBusy = signal(false);
  private readonly requestError = signal('');

  readonly busy = this.requestBusy.asReadonly();
  readonly error = this.requestError.asReadonly();

  constructor() {
    inject(DestroyRef).onDestroy(() => this.abort.abort());
  }

  async submit(
    endpoint: string,
    credentials: Readonly<Record<string, string>>,
  ): Promise<AccessSession | null> {
    if (this.busy() || this.abort.signal.aborted) {
      return null;
    }

    this.requestBusy.set(true);
    this.requestError.set('');

    try {
      const session = await this.api.requestOnce<AccessSession>(endpoint, {
        authenticated: true,
        method: 'POST',
        body: credentials,
        signal: this.abort.signal,
      });
      if (this.abort.signal.aborted) {
        return null;
      }
      return session;
    } catch (error) {
      if (!this.abort.signal.aborted) {
        this.requestError.set(errorMessage(error));
      }
      return null;
    } finally {
      this.requestBusy.set(false);
    }
  }
}
