import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RankedStatusService } from '../ranked-status.service';
import { RANKED_REGIONS, RANKED_SCHEDULE_LABEL, formatRankedRemaining } from '../../../shared/utils/ranked-schedule';
import { NotificationService } from '../../../shared/feedback/notification.service';
import { SearchPreferencesService } from '../settings/search-preferences.service';
import {
  ADVANCED_LOOKUP_OPTIONS, buildSearchCommand, createDefaultSearchFormState,
  getAdvancedLookupOption, SEARCH_MATCH_MODE_OPTIONS,
} from './search-form';
import { SearchService } from './search.service';
import { ADVANCED_FILTER_GROUPS, SONG_TYPE_OPTIONS } from './search-filter-options';
import { SegmentedRadioComponent } from '../../../shared/controls/segmented-radio.component';
import { InfoPopoverComponent } from '../../../shared/controls/info-popover.component';
import { CatalogLabelsPopoverComponent } from './catalog-labels-popover.component';
import { CatalogLabelsService } from './catalog-labels.service';
import { GENRES } from './genres';

@Component({
  selector: 'app-search-bar',
  imports: [FormsModule, SegmentedRadioComponent, InfoPopoverComponent, CatalogLabelsPopoverComponent],
  providers: [CatalogLabelsService],
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SearchBarComponent {
  private readonly searches = inject(SearchService);
  private readonly searchPreferences = inject(SearchPreferencesService);
  private readonly rankedStatusService = inject(RankedStatusService);
  private readonly notifications = inject(NotificationService);

  readonly showAdvancedFilters = computed(
    () => this.searchPreferences.preferences().searchMode === 'advanced',
  );

  readonly form = createDefaultSearchFormState();
  readonly genres = GENRES;
  readonly tags = inject(CatalogLabelsService).getList('/api/tags');
  readonly creditOptionsOpen = signal(false);
  readonly songTypeOptions = SONG_TYPE_OPTIONS;
  readonly advancedFilterGroups = ADVANCED_FILTER_GROUPS;
  readonly rankedStatus = this.rankedStatusService.status;
  readonly rankedRegions = RANKED_REGIONS;
  readonly rankedScheduleLabel = RANKED_SCHEDULE_LABEL;
  readonly formatRankedRemaining = formatRankedRemaining;
  readonly matchModeOptions = SEARCH_MATCH_MODE_OPTIONS;
  readonly advancedLookupOptions = ADVANCED_LOOKUP_OPTIONS;
  readonly getAdvancedLookupOption = getAdvancedLookupOption;
  readonly fieldModes = [
    { id: 'text', label: 'Text' },
    { id: 'lookup', label: 'IDs' },
  ] as const;

  get isCreditIdLookup(): boolean {
    return this.form.advancedLookupType === 'artist-ids'
      || this.form.advancedLookupType === 'composer-ids';
  }

  toggleAdvancedFilters(): void {
    const showAdvancedFilters = !this.showAdvancedFilters();
    this.form.main = '';
    this.searchPreferences.updatePreferences({
      searchMode: showAdvancedFilters ? 'advanced' : 'simple',
    });
  }

  submitSearch(): void {
    const result = buildSearchCommand(
      this.form,
      this.showAdvancedFilters(),
      this.rankedStatus().active,
    );
    if ('error' in result) {
      this.notifications.show(result.error);
      return;
    }

    this.searches.runSearch(result.command);
  }
}
