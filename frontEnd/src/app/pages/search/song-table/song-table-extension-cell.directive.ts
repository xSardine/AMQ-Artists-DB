import { afterRenderEffect, Directive, ElementRef, inject, input, OnDestroy, untracked } from '@angular/core';
import type { AnimeTitleLanguage } from '../settings/search-preferences';
import { DomExtensionOutlet } from '../extensions/dom-extension-outlet';
import type { Song } from '../songs/song';
import type { SongColumnCellContext, SongColumnDefinition } from './song-table-columns';

/** Mounts userscript-owned cell DOM and guarantees its cleanup lifecycle. */
@Directive({
  selector: '[songTableExtensionCell]',
})
export class SongTableExtensionCellDirective implements OnDestroy {
  readonly songTableExtensionCell = input.required<SongColumnDefinition>();
  readonly extensionCellSong = input.required<Song>();
  readonly extensionCellRowIndex = input.required<number>();
  readonly extensionCellAnimeTitleLanguage = input.required<AnimeTitleLanguage>();

  private readonly elementRef = inject(ElementRef<HTMLElement>);
  private readonly outlet = new DomExtensionOutlet(this.elementRef.nativeElement);

  constructor() {
    afterRenderEffect(() => {
      const column = this.songTableExtensionCell();
      const context: SongColumnCellContext = {
        song: this.extensionCellSong(),
        rowIndex: this.extensionCellRowIndex(),
        animeTitleLanguage: this.extensionCellAnimeTitleLanguage(),
      };
      untracked(() => this.mount(column, context));
    });
  }

  ngOnDestroy(): void {
    this.outlet.unmount();
  }

  private mount(
    column: SongColumnDefinition,
    context: SongColumnCellContext,
  ): void {
    const renderCell = column.renderCell;
    if (!renderCell) {
      this.outlet.unmount();
      return;
    }

    this.outlet.mount(
      `custom table column "${column.id}"`,
      (container) => renderCell(container, context),
    );
  }
}
