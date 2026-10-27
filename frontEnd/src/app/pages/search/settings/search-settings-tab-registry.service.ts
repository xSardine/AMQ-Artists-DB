import { computed, Injectable, signal } from '@angular/core';

export type SettingsTabCleanup = () => void;
export type SettingsTabRender = (panel: HTMLElement) => void | SettingsTabCleanup;

export interface SettingsTabDefinition {
  readonly id: string;
  readonly label: string;
  readonly render: SettingsTabRender;
}

const BUILT_IN_TABS = [
  { id: 'settings', label: 'Settings' },
  { id: 'info', label: 'Info' },
] as const;

@Injectable()
export class SearchSettingsTabRegistryService {
  readonly builtInTabs = BUILT_IN_TABS;
  private readonly registeredTabs = signal<SettingsTabDefinition[]>([]);
  readonly extensionTabs = this.registeredTabs.asReadonly();
  readonly tabs = computed(() => [...this.builtInTabs, ...this.extensionTabs()]);

  registerTab(definition: SettingsTabDefinition): SettingsTabCleanup {
    this.validateDefinition(definition);

    if (this.builtInTabs.some((tab) => tab.id === definition.id)) {
      throw new Error(`The settings tab id "${definition.id}" is reserved.`);
    }
    if (this.registeredTabs().some((tab) => tab.id === definition.id)) {
      throw new Error(`A settings tab with id "${definition.id}" is already registered.`);
    }

    const registeredTab = Object.freeze({
      ...definition,
      label: definition.label.trim(),
    });
    this.registeredTabs.update((tabs) => [...tabs, registeredTab]);
    return () => this.unregisterTab(registeredTab);
  }

  getExtensionTab(id: string): SettingsTabDefinition | undefined {
    return this.registeredTabs().find((tab) => tab.id === id);
  }

  private unregisterTab(definition: SettingsTabDefinition): void {
    if (!this.registeredTabs().includes(definition)) return;

    this.registeredTabs.update((tabs) => tabs.filter((tab) => tab !== definition));
  }

  private validateDefinition(definition: SettingsTabDefinition): void {
    if (!definition || typeof definition !== 'object') {
      throw new TypeError('A settings tab definition is required.');
    }
    if (typeof definition.id !== 'string' || !/^[a-z][a-z0-9-]*$/.test(definition.id)) {
      throw new TypeError('Settings tab ids must start with a letter and contain only lowercase letters, numbers, and hyphens.');
    }
    if (typeof definition.label !== 'string' || !definition.label.trim()) {
      throw new TypeError('Settings tab labels cannot be empty.');
    }
    if (typeof definition.render !== 'function') {
      throw new TypeError('Settings tab render must be a function.');
    }
  }
}
