import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { ToolbarComponent } from '../shared/layout/toolbar.component';
import { ModalShellComponent } from '../shared/dialogs/modal-shell.component';
import { ThemeSelectorComponent } from '../shared/controls/theme-selector.component';

@Component({
  imports: [ToolbarComponent, ModalShellComponent, ThemeSelectorComponent],
  host: { style: 'display: block' },
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page-shell">
      <app-toolbar href="/" (settingsRequested)="settingsOpen.set(true)" />
      @if (settingsOpen()) {
        <app-modal-shell modalTitle="Settings" dialogId="not-found-settings-modal" titleId="not-found-settings-title"
          closeButtonId="not-found-settings-close" closeLabel="Close settings" (closed)="settingsOpen.set(false)">
          <div class="settings-layout settings-layout--scroll">
            <div class="settings-rows">
              <div class="settings-row" role="group" aria-labelledby="not-found-settings-theme-label">
                <h3 id="not-found-settings-theme-label" class="settings-row-label">Theme</h3>
                <div class="settings-row-controls">
                  <app-theme-selector controlId="not-found-settings-theme" />
                </div>
              </div>
            </div>
          </div>
        </app-modal-shell>
      }
      <main class="page-content">
        <h1>Page not found</h1>
        <p>This address does not serve a page.</p>
      </main>
    </div>
  `,
})
export class NotFoundComponent {
  readonly settingsOpen = signal(false);
}
