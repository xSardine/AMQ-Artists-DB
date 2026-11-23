import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ConfirmDialogComponent } from '../../shared/dialogs/confirm-dialog.component';
import { ToolbarComponent } from '../../shared/layout/toolbar.component';
import { ContributeSettingsDialogComponent } from './contribute-settings-dialog.component';
import { recordContext, displayValue } from '../../shared/contributions/contribution-format';
import { FIELD_LABELS, isArtistId, profileUrl } from '../../shared/contributions/contribution-fields';
import type { ContributionOperation } from '../../shared/contributions/contribution-types';
import { ContributionDraft } from './contribution-draft';
import { ContributeState } from './contribute-state';

@Component({
  selector: 'app-contribute-page',
  imports: [
    FormsModule,
    ToolbarComponent,
    ContributeSettingsDialogComponent,
    ConfirmDialogComponent,
  ],
  host: { style: 'display: block' },
  providers: [ContributionDraft, ContributeState],
  styleUrl: './contribute-page.component.css',
  templateUrl: './contribute-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContributePageComponent {
  readonly state = inject(ContributeState);
  readonly settingsOpen = signal(false);
  readonly discardOpen = signal(false);
  readonly labels = FIELD_LABELS;
  readonly operationLabels: Record<ContributionOperation, string> = {
    set: 'Set / correct',
    clear: 'Clear value',
    add_alias: 'Add alias',
    replace_alias: 'Replace alias',
    remove_alias: 'Remove alias',
  };
  readonly display = displayValue;
  readonly recordContext = recordContext;
  readonly isArtistId = isArtistId;
  readonly profileUrl = profileUrl;
  readonly maxArtistId = Number.MAX_SAFE_INTEGER;

  editChange(clientId: string, editor: HTMLElement): void {
    this.state.edit(clientId);
    if (this.state.draft.editingId() === clientId) editor.focus();
  }

  discardDraft(): void {
    if (!this.state.submitting()) this.discardOpen.set(true);
  }

  confirmDiscard(): void {
    if (this.state.submitting() || !this.discardOpen()) return;
    this.state.discardDraft();
    this.discardOpen.set(false);
  }
}
