import { DestroyRef, inject, Injectable, signal } from '@angular/core';

export interface StorageDefinition<T> {
  key: string;
  defaults: () => T;
  parse: (value: unknown) => T;
  /** Recover valid current fields when reading damaged or incomplete browser data. */
  recover?: (value: unknown) => T;
  syncAcrossTabs?: boolean;
  rawString?: boolean;
}

export interface StorageEntry {
  readonly key: string;
  settled(): Promise<void>;
  externalChange(): void;
}

export interface StorageReplacement {
  entry: StorageEntry;
  raw: string;
  accept: () => void;
}

@Injectable({ providedIn: 'root' })
export class BrowserStorage {
  private readonly records = new Map<string, StorageEntry>();

  constructor() {
    const listener = (event: StorageEvent) => {
      try {
        if (event.storageArea !== localStorage) return;
      } catch {
        return;
      }
      for (const entry of this.records.values()) {
        if (event.key === null || event.key === entry.key) entry.externalChange();
      }
    };
    window.addEventListener('storage', listener);
    inject(DestroyRef).onDestroy(() => {
      window.removeEventListener('storage', listener);
    });
  }

  record<T>(definition: StorageDefinition<T>): BrowserRecord<T> {
    const existing = this.records.get(definition.key);
    if (existing) return existing as BrowserRecord<T>;
    const record = new BrowserRecord(this, definition);
    this.records.set(definition.key, record);
    return record;
  }

  async locked<T>(operation: () => T): Promise<T> {
    if (navigator.locks) {
      return navigator.locks.request('anisongdb-browser-data', operation);
    }
    return operation();
  }

  async settle(): Promise<void> {
    await Promise.all(Array.from(this.records.values(), entry => entry.settled()));
  }

  async replace(replacements: StorageReplacement[]): Promise<void> {
    await this.settle();
    await this.locked(() => {
      const previous = replacements.map(item => localStorage.getItem(item.entry.key));
      try {
        for (const item of replacements) localStorage.setItem(item.entry.key, item.raw);
      } catch {
        let restored = true;
        replacements.forEach((item, index) => {
          try {
            const raw = previous[index];
            if (raw === null) localStorage.removeItem(item.entry.key);
            else localStorage.setItem(item.entry.key, raw);
          } catch {
            restored = false;
          }
        });
        if (!restored) {
          for (const item of replacements) item.entry.externalChange();
          throw new Error('Import failed and some previous data could not be restored. Export your current data before reloading.');
        }
        throw new Error('Could not save the replacement. Previous saved data was restored.');
      }
      for (const item of replacements) item.accept();
    });
  }
}

export class BrowserRecord<T> implements StorageEntry {
  readonly key: string;
  private readonly valueSignal;
  readonly value;
  private expectedRaw: string | null = null;
  private dirty = false;
  private failedSave = false;
  private externalPending = false;
  private revision = 0;
  private replacedThrough = 0;
  private pending = 0;
  private queue: Promise<void> = Promise.resolve();

  constructor(private readonly storage: BrowserStorage, readonly definition: StorageDefinition<T>) {
    this.key = definition.key;
    this.valueSignal = signal(definition.defaults());
    this.value = this.valueSignal.asReadonly();
    this.readSaved();
  }

  update(change: (value: T) => T): void {
    const next = this.definition.parse(change(this.value()));
    this.valueSignal.set(next);
    this.dirty = true;
    this.enqueue(next, change);
  }

  set(value: T): void {
    this.update(() => value);
  }

  settled(): Promise<void> {
    return this.queue;
  }

  externalChange(): void {
    // An open contribution editor keeps its own draft until reload.
    if (this.definition.syncAcrossTabs === false) return;
    if (this.pending) {
      this.externalPending = true;
      return;
    }
    try {
      if (localStorage.getItem(this.key) === this.expectedRaw) return;
    } catch {
      return;
    }
    if (!this.dirty) this.readSaved();
  }

  /** Called only after a complete backup replacement has been written. */
  acceptSaved(value: T): void {
    this.replacedThrough = ++this.revision;
    this.valueSignal.set(value);
    this.expectedRaw = this.encode(value);
    this.dirty = false;
    this.failedSave = false;
  }

  private encode(value: T): string {
    return this.definition.rawString ? String(value) : JSON.stringify(value);
  }

  replacement(value: T): StorageReplacement {
    const parsed = this.definition.parse(value);
    return { entry: this, raw: this.encode(parsed), accept: () => this.acceptSaved(parsed) };
  }

  private decode(raw: string | null): T {
    if (raw === null) return this.definition.defaults();
    let value: unknown;
    try {
      value = this.definition.rawString ? raw : JSON.parse(raw);
    } catch {
      return this.definition.defaults();
    }
    try {
      return this.definition.parse(value);
    } catch {
      try {
        return this.definition.recover
          ? this.definition.parse(this.definition.recover(value))
          : this.definition.defaults();
      } catch {
        return this.definition.defaults();
      }
    }
  }

  private readSaved(): void {
    let raw: string | null;
    try {
      raw = localStorage.getItem(this.key);
    } catch {
      return;
    }
    try {
      const value = this.decode(raw);
      this.valueSignal.set(value);
      this.expectedRaw = raw;
      this.dirty = false;
      this.failedSave = false;
      // Quietly replace invalid fields so they do not break future saves.
      if (raw !== null && this.encode(value) !== raw) this.enqueue(value, current => current);
    } catch {
      // Storage is optional; the current in-memory value remains usable.
    }
  }

  private enqueue(next: T, change: (value: T) => T): void {
    const revision = ++this.revision;
    this.pending++;
    this.queue = this.queue.then(async () => {
      try {
        await this.storage.locked(() => {
          if (revision <= this.replacedThrough) return;
          if (this.definition.syncAcrossTabs === false && revision !== this.revision) return;
          const raw = localStorage.getItem(this.key);
          let value = next;
          if (this.definition.syncAcrossTabs !== false && !this.failedSave) {
            // Apply each queued edit to the latest saved value, retaining other tabs' fields.
            value = this.definition.parse(change(this.decode(raw)));
          }
          const encoded = this.encode(value);
          localStorage.setItem(this.key, encoded);
          this.expectedRaw = encoded;
          if (revision === this.revision) {
            this.valueSignal.set(value);
            this.dirty = false;
            this.failedSave = false;
          }
        });
      } catch {
        // Keep the complete local value. The next edit attempts to save it again.
        this.failedSave = true;
      } finally {
        this.pending--;
        if (!this.pending && this.externalPending) {
          this.externalPending = false;
          this.externalChange();
        }
      }
    });
  }
}
