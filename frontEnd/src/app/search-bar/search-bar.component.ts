import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { SearchRequestService } from '../core/services/search-request.service';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-search-bar',
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.css'],
  standalone: false,
})
export class SearchBarComponent implements OnInit, OnDestroy {
  constructor(
    private sanitizer: DomSanitizer,
    private searchRequestService: SearchRequestService
  ) {}

  @Input() previousBody: any;
  @Input() currentSongList: any;

  @Output() sendSongListtoTable = new EventEmitter();
  sendSongList(currentSongList: any) {
    this.sendSongListtoTable.emit(currentSongList);
  }

  @Output() sendPreviousBody = new EventEmitter();
  sendPrevBody(body: any) {
    this.sendPreviousBody.emit(body);
  }

  mainFilter: string = '';
  animeFilter: string = '';
  songNameFilter: string = '';
  artistFilter: string = '';
  composerFilter: string = '';
  maximumRandomsFilter: string = '99';
  minimalMembersFilter: string = '0';
  selectedCombination: string = 'Union (OR)';
  mainFilterPartialMatch: boolean = true;
  animeFilterPartialMatch: boolean = true;
  songNameFilterPartialMatch: boolean = true;
  artistFilterPartialMatch: boolean = true;
  composerFilterPartialMatch: boolean = true;
  composerFilterArrangement: boolean = true;
  ignoreDuplicate: boolean = false;
  showOpenings: boolean = true;
  showEndings: boolean = true;
  showInserts: boolean = true;
  showNormalBroadcasts: boolean = true;
  showDubs: boolean = true;
  showRebroadcasts: boolean = true;
  showStandards: boolean = true;
  showInstrumentals: boolean = true;
  showChantings: boolean = true;
  showCharacters: boolean = true;
  showTv: boolean = true;
  showMovie: boolean = true;
  showOva: boolean = true;
  showOna: boolean = true;
  showSpecial: boolean = true;
  showDoujin: boolean = true;
  showAdvancedFilters: boolean = false;

  rankedTime = false;
  rankedRegion: string | null = null;
  rankedRemainingMinutes = 0;
  private rankedCountdownTimer: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.refreshRankedStatus();
    this.rankedCountdownTimer = setInterval(() => this.refreshRankedStatus(), 1000);
    this.currentSongList = this.searchRequestService
      .getFirstNRequest()
      .subscribe((data) => {
        this.currentSongList = data;
        this.sendSongList(this.currentSongList);
      });
  }

  ngOnDestroy(): void {
    if (this.rankedCountdownTimer !== null) {
      clearInterval(this.rankedCountdownTimer);
    }
  }

  private refreshRankedStatus(): void {
    const status = this.searchRequestService.getRankedStatus();
    this.rankedTime = status.active;
    this.rankedRegion = status.region;
    this.rankedRemainingMinutes = status.remainingMinutes;
  }

  private songFilterOptions() {
    return {
      opening_filter: this.showOpenings,
      ending_filter: this.showEndings,
      insert_filter: this.showInserts,
      normal_broadcast: this.showNormalBroadcasts,
      dub: this.showDubs,
      rebroadcast: this.showRebroadcasts,
      standard: this.showStandards,
      instrumental: this.showInstrumentals,
      chanting: this.showChantings,
      character: this.showCharacters,
      tv_filter: this.showTv,
      movie_filter: this.showMovie,
      ova_filter: this.showOva,
      ona_filter: this.showOna,
      special_filter: this.showSpecial,
      doujin_filter: this.showDoujin,
    };
  }

  // Returns the season string if text matches formats like "Winter 2024" (case-insensitive), otherwise null
  private parseSeasonQuery(text: string): string | null {
    text = text.trim();
    if (/^(winter|spring|summer|fall) (\d{4})$/i.test(text)) {
      return text;
    }
    return null;
  }

  onSearchCallKey(): void {
    let body: any;
    let tmp_anime_filter,
      tmp_songname_filter,
      tmp_artist_filter,
      tmp_composer_filter;
    let tmp_select = false;

    this.refreshRankedStatus();

    if (this.selectedCombination == 'Intersection (AND)') {
      tmp_select = true;
    }

    if (this.showAdvancedFilters) {
      if (this.animeFilter.length > 0) {
        tmp_anime_filter = {
          search: this.animeFilter,
          partial_match: this.animeFilterPartialMatch,
        };
      } else {
        tmp_anime_filter = undefined;
      }

      if (this.songNameFilter.length > 0) {
        tmp_songname_filter = {
          search: this.songNameFilter,
          partial_match: this.songNameFilterPartialMatch,
        };
      } else {
        tmp_songname_filter = undefined;
      }

      if (this.artistFilter.length > 0) {
        if (!this.minimalMembersFilter) {
          this.minimalMembersFilter = '0';
        }
        if (!this.maximumRandomsFilter) {
          this.maximumRandomsFilter = '99';
        }
        tmp_artist_filter = {
          search: this.artistFilter,
          partial_match: this.artistFilterPartialMatch,
          group_granularity: parseInt(this.minimalMembersFilter),
          max_other_artist: parseInt(this.maximumRandomsFilter),
        };
      } else {
        tmp_artist_filter = undefined;
      }

      if (this.composerFilter.length > 0) {
        if (!this.minimalMembersFilter) {
          this.minimalMembersFilter = '0';
        }
        if (!this.maximumRandomsFilter) {
          this.maximumRandomsFilter = '99';
        }
        tmp_composer_filter = {
          search: this.composerFilter,
          partial_match: this.composerFilterPartialMatch,
          arrangement: this.composerFilterArrangement,
          group_granularity: parseInt(this.minimalMembersFilter),
          max_other_artist: parseInt(this.maximumRandomsFilter),
        };
      } else {
        tmp_composer_filter = undefined;
      }

      body = {
        anime_search_filter: tmp_anime_filter,
        song_name_search_filter: tmp_songname_filter,
        artist_search_filter: tmp_artist_filter,
        composer_search_filter: tmp_composer_filter,
        and_logic: tmp_select,
        ignore_duplicate: this.ignoreDuplicate,
        ...this.songFilterOptions(),
      };
    } else {
      const season = this.parseSeasonQuery(this.mainFilter);
      if (season) {
        body = {
          season,
          ignore_duplicate: this.ignoreDuplicate,
          ...this.songFilterOptions(),
        };
      } else if (this.mainFilter.length == 0) {
        body = {
          anime_search_filter: undefined,
          song_name_search_filter: undefined,
          artist_search_filter: undefined,
          composer_search_filter: undefined,
          and_logic: tmp_select,
          ignore_duplicate: this.ignoreDuplicate,
          ...this.songFilterOptions(),
        };
      } else if (this.rankedTime) {
        body = {
          anime_search_filter: {
            search: this.mainFilter,
            partial_match: this.mainFilterPartialMatch,
          },
          song_name_search_filter: undefined,
          artist_search_filter: undefined,
          composer_search_filter: undefined,
          and_logic: tmp_select,
          ignore_duplicate: this.ignoreDuplicate,
          ...this.songFilterOptions(),
        };
      } else {
        body = {
          anime_search_filter: {
            search: this.mainFilter,
            partial_match: this.mainFilterPartialMatch,
          },
          song_name_search_filter: {
            search: this.mainFilter,
            partial_match: this.mainFilterPartialMatch,
          },
          artist_search_filter: {
            search: this.mainFilter,
            partial_match: this.mainFilterPartialMatch,
            group_granularity: parseInt(this.minimalMembersFilter),
            max_other_artist: parseInt(this.maximumRandomsFilter),
          },
          composer_search_filter: {
            search: this.mainFilter,
            partial_match: this.mainFilterPartialMatch,
            arrangement: this.composerFilterArrangement,
          },
          and_logic: tmp_select,
          ignore_duplicate: this.ignoreDuplicate,
          ...this.songFilterOptions(),
        };
      }
    }

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return;
    }

    this.previousBody = body;
    this.sendPrevBody(body);

    const request$ = body.season
      ? this.searchRequestService.seasonRequest(body)
      : this.searchRequestService.searchRequest(body);

    this.currentSongList = request$.subscribe((data) => {
      this.currentSongList = data;
      this.sendSongList(this.currentSongList);
    });
  }

  selectFilterCombinationChangeHandler(event: any) {
    this.selectedCombination = event.target.value;
  }

  downloadJsonHref: SafeUrl = '';
  downloadFileName: string = 'Init_SongList.json';

  openJsonHelp() {
    window.open(
      'https://github.com/xSardine/AMQ-Artists-DB/tree/main/misc_scripts#misc-scripts',
      '_blank',
      'noopener',
    );
  }

  generateDownloadJsonUri() {
    // Use template literals and the `join` method to generate the file name
    this.downloadFileName = [
      this.showAdvancedFilters
        ? [
            this.animeFilter,
            this.songNameFilter,
            this.artistFilter,
            this.composerFilter,
          ]
        : this.mainFilter,
      'SongList.json',
    ]
      .join('_')
      .replace(/ /g, '')
      .replace(/,/g, '_')
      .replace(/__/g, '');

    // Stringify the JSON data and create a blob
    let theJSON = JSON.stringify(this.currentSongList);
    let blob = new Blob([theJSON], { type: 'text/json' });

    // Create a URL for the blob and sanitize it
    let url = window.URL.createObjectURL(blob);
    let uri = this.sanitizer.bypassSecurityTrustUrl(url);

    // Set the `downloadJsonHref` property to the sanitized URL
    this.downloadJsonHref = uri;
  }
}
