import { Component, OnInit, Output, EventEmitter } from '@angular/core';
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

  mainFilter: string = "";
  animeFilter: string = "";
  songNameFilter: string = "";
  artistFilter: string = "";
  composerFilter: string = "";
  maximumRandomsFilter: string = "99";
  minimalMembersFilter: string = "0";
  selectedCombination: string = "Union";
  animeFilterPartialMatch: boolean = true;
  animeFilterIgnoreSpecialCaracters: boolean = true;
  animeFilterCaseSensitive: boolean = false;
  songNameFilterPartialMatch: boolean = true;
  songNameFilterIgnoreSpecialCaracters: boolean = true;
  songNameFilterCaseSensitive: boolean = false;
  artistFilterPartialMatch: boolean = true;
  artistFilterIgnoreSpecialCaracters: boolean = true;
  artistFilterCaseSensitive: boolean = false;
  composerFilterPartialMatch: boolean = true;
  composerFilterIgnoreSpecialCaracters: boolean = true;
  composerFilterCaseSensitive: boolean = false;
  composerFilterArrangement: boolean = false;
  ignoreDuplicate: boolean = false;
  showOpenings: boolean = true;
  showEndings: boolean = true;
  showInserts: boolean = true;
  showAdvancedFilters: boolean = false;

  rankedTime = false;
  RankedDisabledTimeLeft = 0

  currentSongList: object = []

  checkRankedTime() {
    let date = new Date()
    let hour = date.getUTCHours()
    let minute = date.getUTCMinutes()

    // 20:30 CST   -> 20:30 CET      -> 20:30 JST (all converted to UTC)
    // West Ranked -> Central Ranked -> East Ranked first half
    if ((hour == 1 && minute >= 30) || (hour == 18 && minute >= 30) || (hour == 11 && minute >= 30)) {
      this.RankedDisabledTimeLeft = 91 - minute
      return true
    }
    // 21:30 CST   -> 21:30 CET      -> 21:30 JST (all converted to UTC)
    // West Ranked -> Central Ranked -> East Ranked second half
    else if ((hour == 2 && minute <= 30) || (hour == 19 && minute <= 30) || (hour == 12 && minute <= 30)) {
      this.RankedDisabledTimeLeft = 31 - minute
      return true
    }
    return false

  }

  ngOnInit(): void {

    if (this.checkRankedTime()) {
      this.rankedTime = true;
    }
    else {
      this.rankedTime = false;
    }

    this.currentSongList = this.searchRequestService.getFirstNRequest().subscribe(data => {
      this.currentSongList = data
      this.sendMessage(this.currentSongList)
    });
  }

  onSearchCallKey(): void {

    let body = {};
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
          "ignore_special_character": this.animeFilterIgnoreSpecialCaracters,
          "partial_match": this.animeFilterPartialMatch,
          "case_sensitive": this.animeFilterCaseSensitive,
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
          "ignore_special_character": this.animeFilterIgnoreSpecialCaracters,
          "partial_match": this.animeFilterPartialMatch,
          "case_sensitive": this.animeFilterCaseSensitive,
        }
      }
      else {
        tmp_anime_filter = undefined;
      }

      if (this.songNameFilter.length > 0) {
        tmp_songname_filter = {
          "search": this.songNameFilter,
          "ignore_special_character": this.songNameFilterIgnoreSpecialCaracters,
          "partial_match": this.songNameFilterPartialMatch,
          "case_sensitive": this.songNameFilterCaseSensitive,
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
          "ignore_special_character": this.artistFilterIgnoreSpecialCaracters,
          "partial_match": this.artistFilterPartialMatch,
          "case_sensitive": this.artistFilterCaseSensitive,
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
          "ignore_special_character": this.composerFilterIgnoreSpecialCaracters,
          "partial_match": this.composerFilterPartialMatch,
          "case_sensitive": this.composerFilterCaseSensitive,
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
            "ignore_special_character": this.animeFilterIgnoreSpecialCaracters,
            "partial_match": this.animeFilterPartialMatch,
            "case_sensitive": this.animeFilterCaseSensitive,
          },
          "song_name_search_filter": {
            "search": this.mainFilter,
            "ignore_special_character": this.songNameFilterIgnoreSpecialCaracters,
            "partial_match": this.songNameFilterPartialMatch,
            "case_sensitive": this.songNameFilterCaseSensitive,
          },
          "artist_search_filter": {
            "search": this.mainFilter,
            "ignore_special_character": this.artistFilterIgnoreSpecialCaracters,
            "partial_match": this.artistFilterPartialMatch,
            "case_sensitive": this.artistFilterCaseSensitive,
            "group_granularity": parseInt(this.minimalMembersFilter),
            "max_other_artist": parseInt(this.maximumRandomsFilter),
          },
          "composer_search_filter": {
            "search": this.mainFilter,
            "ignore_special_character": this.composerFilterIgnoreSpecialCaracters,
            "partial_match": this.composerFilterPartialMatch,
            "case_sensitive": this.composerFilterCaseSensitive,
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

    this.currentSongList = this.searchRequestService.searchRequest(body).subscribe(data => {
      this.currentSongList = data
      this.sendMessage(this.currentSongList)
    });
  }

  selectFilterCombinationChangeHandler(event: any) {
    this.selectedCombination = event.target.value;
  }

  downloadJsonHref: SafeUrl = ''
  downloadFileName: string = "Init_SongList.json"

  generateDownloadJsonUri() {

    if (!this.showAdvancedFilters) {
      this.downloadFileName = this.mainFilter.replace(" ", "") + "_SongList.json"
    }
    else {
      this.downloadFileName = this.animeFilter.replace(" ", "") + "_" + this.songNameFilter.replace(" ", "") + "_" + this.artistFilter.replace(" ", "") + "_SongList.json"
    }
    let theJSON = JSON.stringify(this.currentSongList);
    let blob = new Blob([theJSON], { type: 'text/json' });
    let url = window.URL.createObjectURL(blob);
    let uri: SafeUrl = this.sanitizer.bypassSecurityTrustUrl(url);
    this.downloadJsonHref = uri;
  }

  @Output() sendSongListtoTable = new EventEmitter();

  sendMessage(currentSongList: any) {
    this.sendSongListtoTable.emit(currentSongList)
  }

}
