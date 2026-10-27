import { afterRenderEffect, Directive, ElementRef, inject, input, OnDestroy, untracked } from '@angular/core';
import { SearchSettingsTabRegistryService } from './search-settings-tab-registry.service';
import type { SettingsTabDefinition } from './search-settings-tab-registry.service';
import { DomExtensionOutlet } from '../extensions/dom-extension-outlet';

/** Mounts a userscript tab's DOM and owns its render cleanup lifecycle. */
@Directive({
  selector: '[settingsTabPanel]',
})
export class SettingsTabPanelDirective implements OnDestroy {
  readonly settingsTabPanel = input.required<string>();

  private readonly elementRef = inject(ElementRef<HTMLElement>);
  private readonly tabRegistry = inject(SearchSettingsTabRegistryService);
  private readonly outlet = new DomExtensionOutlet(this.elementRef.nativeElement);
  private mountedDefinition?: SettingsTabDefinition;

  constructor() {
    afterRenderEffect(() => {
      const definition = this.tabRegistry.getExtensionTab(this.settingsTabPanel());
      untracked(() => this.mount(definition));
    });
  }

  ngOnDestroy(): void {
    this.outlet.unmount();
  }

  private mount(definition: SettingsTabDefinition | undefined): void {
    if (definition === this.mountedDefinition) return;

    this.mountedDefinition = undefined;
    if (!definition) {
      this.outlet.unmount();
      return;
    }

    if (this.outlet.mount(
      `settings tab "${definition.id}"`,
      definition.render,
    )) {
      this.mountedDefinition = definition;
    }
  }
}
