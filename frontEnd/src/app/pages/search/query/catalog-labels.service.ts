import { DestroyRef, inject, Injectable, signal, Signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { ApiClient, errorMessage } from '../../../core/api-client.service';

interface CatalogLabelList {
  readonly values: Signal<readonly string[] | null>;
  readonly loading: Signal<boolean>;
  readonly error: Signal<string>;
  load(): void;
}

@Injectable()
export class CatalogLabelsService {
  private readonly api = inject(ApiClient);
  private readonly destroyRef = inject(DestroyRef);
  private readonly lists = new Map<string, CatalogLabelList>();

  getList(endpoint: string): CatalogLabelList {
    const existing = this.lists.get(endpoint);
    if (existing) return existing;

    const values = signal<readonly string[] | null>(null);
    const loading = signal(false);
    const error = signal('');
    const list: CatalogLabelList = {
      values: values.asReadonly(),
      loading: loading.asReadonly(),
      error: error.asReadonly(),
      load: () => {
        if (values() !== null || loading()) return;
        loading.set(true);
        error.set('');
        this.api.request<string[]>(endpoint).pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => loading.set(false)),
        ).subscribe({
          next: names => values.set(names),
          error: (cause: unknown) => error.set(errorMessage(cause)),
        });
      },
    };
    this.lists.set(endpoint, list);
    return list;
  }
}
