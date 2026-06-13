import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { Observable, Subscription } from 'rxjs';
import { RankedStatus, SearchRequestService } from '../core/services/search-request.service';
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
    readonly searchRequestService: SearchRequestService,
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

  rankedStatus: RankedStatus = {
    active: false,
    region: null,
    remainingSeconds: 0,
  };
  private rankedStatusSubscription: Subscription | null = null;

  ngOnInit(): void {
    this.rankedStatusSubscription = this.searchRequestService.rankedStatus$.subscribe(
      (status) => {
        this.rankedStatus = status;
      },
    );
    this.currentSongList = this.searchRequestService
      .getFirstNRequest()
      .subscribe((data) => {
        this.currentSongList = data;
        this.sendSongList(this.currentSongList);
      });
  }

  ngOnDestroy(): void {
    this.rankedStatusSubscription?.unsubscribe();
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
    const match = text.trim().match(/^(winter|spring|summer|fall)\s*(\d{4})$/i);
    if (!match) {
      return null;
    }
    return `${match[1]} ${match[2]}`;
  }

  // Parses queries for ANN, MAL, ANN Song, or AMQ Song IDs with their respective keywords
  private parseIdListQuery(
    text: string,
  ): { field: 'ann_ids' | 'mal_ids' | 'ann_song_ids' | 'amq_song_ids'; ids: number[] } | null {
    const match = text.trim().match(/^(annid|malid|annsongid|amqsongid)\s+(.+)$/i);
    if (!match) {
      return null;
    }

    const ids = [...match[2].matchAll(/\d+/g)].map((part) => parseInt(part[0], 10));
    if (!ids.length) {
      return null;
    }

    const fieldByKeyword: Record<string, 'ann_ids' | 'mal_ids' | 'ann_song_ids' | 'amq_song_ids'> = {
      annid: 'ann_ids',
      malid: 'mal_ids',
      annsongid: 'ann_song_ids',
      amqsongid: 'amq_song_ids',
    };

    return { field: fieldByKeyword[match[1].toLowerCase()], ids };
  }

  private searchRequestForBody(body: any): Observable<any> {
    if (body.season) {
      return this.searchRequestService.seasonRequest(body);
    }
    if (body.ann_ids) {
      return this.searchRequestService.annIdsSearchRequest(body);
    }
    if (body.mal_ids) {
      return this.searchRequestService.malIdsSearchRequest(body);
    }
    if (body.ann_song_ids) {
      return this.searchRequestService.annSongIdsSearchRequest(body);
    }
    if (body.amq_song_ids) {
      return this.searchRequestService.amqSongIdsSearchRequest(body);
    }
    return this.searchRequestService.searchRequest(body);
  }

  onSearchCallKey(): void {
    let body: any;
    let tmp_anime_filter,
      tmp_songname_filter,
      tmp_artist_filter,
      tmp_composer_filter;
    let tmp_select = false;

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
      const idList = this.parseIdListQuery(this.mainFilter);
      if (season) {
        body = {
          season,
          ignore_duplicate: this.ignoreDuplicate,
          ...this.songFilterOptions(),
        };
      } else if (idList) {
        body = {
          [idList.field]: idList.ids,
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
      } else if (this.rankedStatus.active) {
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

    const request$ = this.searchRequestForBody(body);

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
