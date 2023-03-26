import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { SearchRequestService } from '../core/services/search-request.service';
import { DomSanitizer, SafeResourceUrl, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-search-bar',
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.css'],
})
export class SearchBarComponent implements OnInit {

  constructor(private sanitizer: DomSanitizer, private searchRequestService: SearchRequestService) {
  }

  @Input() previousBody: any
  @Input() currentSongList: any

  @Output() sendSongListtoTable = new EventEmitter();
  sendSongList(currentSongList: any) {
    this.sendSongListtoTable.emit(currentSongList)
  }

  @Output() sendPreviousBody = new EventEmitter();
  sendPrevBody(body: any) {
    this.sendPreviousBody.emit(body)
  }

  mainFilter: string = "";
  animeFilter: string = "";
  songNameFilter: string = "";
  artistFilter: string = "";
  composerFilter: string = "";
  maximumRandomsFilter: string = "99";
  minimalMembersFilter: string = "0";
  selectedCombination: string = "Union";
  animeFilterPartialMatch: boolean = true;
  songNameFilterPartialMatch: boolean = true;
  artistFilterPartialMatch: boolean = true;
  composerFilterPartialMatch: boolean = true;
  composerFilterArrangement: boolean = true;
  ignoreDuplicate: boolean = false;
  showOpenings: boolean = true;
  showEndings: boolean = true;
  showInserts: boolean = true;
  showAdvancedFilters: boolean = false;

  rankedTime = false;
  RankedDisabledTimeLeft = 0

  checkRankedTime() {

    // Define the ranked time intervals as an array of objects
    let rankedTimeIntervals = [
      //CST NA
      {
        start: new Date().setUTCHours(1, 30, 0, 0),
        end: new Date().setUTCHours(2, 28, 0, 0)
      },
      //JST Asia
      {
        start: new Date().setUTCHours(11, 30, 0, 0),
        end: new Date().setUTCHours(12, 28, 0, 0)
      },
      // CET EU
      {
        start: new Date().setUTCHours(20, 30, 0, 0),
        end: new Date().setUTCHours(21, 28, 0, 0)
      }
    ];

    // Get the current time in the user's local time zone
    let date = Date.now();

    // Find the ranked time interval that the current time is within
    let rankedTimeInterval = rankedTimeIntervals.find(interval => {
      return date >= interval.start && date < interval.end;
    });

    // If a ranked time interval was found, calculate the amount of time left until the end of the ranked period
    if (rankedTimeInterval) {
      this.RankedDisabledTimeLeft = Math.ceil((rankedTimeInterval.end - date) / 1000 / 60);
      return true;
    }

    return false;


  }

  ngOnInit(): void {
    this.rankedTime = this.checkRankedTime()
    this.currentSongList = this.searchRequestService.getFirstNRequest().subscribe(data => {
      this.currentSongList = data
      this.sendSongList(this.currentSongList)
    });
  }

  onSearchCallKey(): void {

    let body: any;
    let tmp_anime_filter, tmp_songname_filter, tmp_artist_filter, tmp_composer_filter;
    let tmp_select = false;

    if (this.checkRankedTime()) {
      this.rankedTime = true;
    }
    else {
      this.rankedTime = false;
    }

    if (this.selectedCombination == "Intersection") {
      tmp_select = true;
    }


    if (this.rankedTime) {

      if (this.animeFilter.length > 0) {
        tmp_anime_filter = {
          "search": this.animeFilter,
          "partial_match": this.animeFilterPartialMatch,
        }
      }
      else {
        tmp_anime_filter = undefined;
      }

      body = {
        "anime_search_filter": tmp_anime_filter,
        "and_logic": tmp_select,
        "ignore_duplicate": this.ignoreDuplicate,
        "opening_filter": this.showOpenings,
        "ending_filter": this.showEndings,
        "insert_filter": this.showInserts,
      }

    }
    else if (this.showAdvancedFilters) {

      if (this.animeFilter.length > 0) {
        tmp_anime_filter = {
          "search": this.animeFilter,
          "partial_match": this.animeFilterPartialMatch,
        }
      }
      else {
        tmp_anime_filter = undefined;
      }

      if (this.songNameFilter.length > 0) {
        tmp_songname_filter = {
          "search": this.songNameFilter,
          "partial_match": this.songNameFilterPartialMatch,
        }
      }
      else {
        tmp_songname_filter = undefined;
      }

      if (this.artistFilter.length > 0) {
        if (!this.minimalMembersFilter) {
          this.minimalMembersFilter = "0"
        }
        if (!this.maximumRandomsFilter) {
          this.maximumRandomsFilter = "99"
        }
        tmp_artist_filter = {
          "search": this.artistFilter,
          "partial_match": this.artistFilterPartialMatch,
          "group_granularity": parseInt(this.minimalMembersFilter),
          "max_other_artist": parseInt(this.maximumRandomsFilter),
        }
      }
      else {
        tmp_artist_filter = undefined;
      }

      if (this.composerFilter.length > 0) {
        tmp_composer_filter = {
          "search": this.composerFilter,
          "partial_match": this.composerFilterPartialMatch,
          "arrangement": this.composerFilterArrangement,
        }
      }
      else {
        tmp_composer_filter = undefined;
      }

      body = {
        "anime_search_filter": tmp_anime_filter,
        "song_name_search_filter": tmp_songname_filter,
        "artist_search_filter": tmp_artist_filter,
        "composer_search_filter": tmp_composer_filter,
        "and_logic": tmp_select,
        "ignore_duplicate": this.ignoreDuplicate,
        "opening_filter": this.showOpenings,
        "ending_filter": this.showEndings,
        "insert_filter": this.showInserts,
      }

    }
    else {

      if (this.mainFilter.length == 0) {
        body = {
          "anime_search_filter": undefined,
          "song_name_search_filter": undefined,
          "artist_search_filter": undefined,
          "composer_search_filter": undefined,
          "and_logic": tmp_select,
          "ignore_duplicate": this.ignoreDuplicate,
          "opening_filter": this.showOpenings,
          "ending_filter": this.showEndings,
          "insert_filter": this.showInserts,
        }
      }
      else {

        body = {
          "anime_search_filter": {
            "search": this.mainFilter,
            "partial_match": this.animeFilterPartialMatch,
          },
          "song_name_search_filter": {
            "search": this.mainFilter,
            "partial_match": this.songNameFilterPartialMatch,
          },
          "artist_search_filter": {
            "search": this.mainFilter,
            "partial_match": this.artistFilterPartialMatch,
            "group_granularity": parseInt(this.minimalMembersFilter),
            "max_other_artist": parseInt(this.maximumRandomsFilter),
          },
          "composer_search_filter": {
            "search": this.mainFilter,
            "partial_match": this.composerFilterPartialMatch,
            "arrangement": this.composerFilterArrangement,
          },
          "and_logic": tmp_select,
          "ignore_duplicate": this.ignoreDuplicate,
          "opening_filter": this.showOpenings,
          "ending_filter": this.showEndings,
          "insert_filter": this.showInserts,
        }
      }
    }

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return
    }

    this.previousBody = body
    this.sendPrevBody(body)

    this.currentSongList = this.searchRequestService.searchRequest(body).subscribe(data => {
      this.currentSongList = data
      this.sendSongList(this.currentSongList)
    });
  }

  selectFilterCombinationChangeHandler(event: any) {
    this.selectedCombination = event.target.value;
  }

  downloadJsonHref: SafeUrl = ''
  downloadFileName: string = "Init_SongList.json"

  generateDownloadJsonUri() {

    // Use template literals and the `join` method to generate the file name
    this.downloadFileName = [
      this.showAdvancedFilters ? [this.animeFilter, this.songNameFilter, this.artistFilter, this.composerFilter] : this.mainFilter,
      "SongList.json"
    ].join("_").replace(/ /g, "").replace(/,/g, "_").replace(/__/g, "");


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
