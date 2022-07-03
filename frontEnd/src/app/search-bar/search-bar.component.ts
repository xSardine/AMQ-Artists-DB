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
      this.sendSongList(this.currentSongList)
    });
  }

  areBodyIdenticalBaseSearch(body: any, body2: any): boolean {

    // if there wasn't any search prior to that
    if (!this.previousBody) {
      return false
    }

    // If the search filters used are different
    if ((body.anime_search_filter && !body2.anime_search_filter)
      || (!body.anime_search_filter && body2.anime_search_filter)
      || (body.artist_search_filter && !body2.artist_search_filter)
      || (!body.artist_search_filter && body2.artist_search_filter)
      || (body.song_name_search_filter && !body2.song_name_search_filter)
      || (!body.song_name_search_filter && body2.song_name_search_filter)
      || (body.composer_search_filter && !body2.composer_search_filter)
      || (!body.composer_search_filter && body2.composer_search_filter)) {
      return false
    }

    // if the general settings are different
    if (body.and_logic != body2.and_logic
      || body.ending_filter != body2.ending_filter
      || body.insert_filter != body2.insert_filter
      || body.opening_filter != body2.opening_filter
      || body.ignore_duplicate != body2.ignore_duplicate) {
      return false
    }

    // if the anime filters are different
    if (body.anime_search_filter && body2.anime_search_filter
      && (body.anime_search_filter.search != body2.anime_search_filter.search
        || body.anime_search_filter.ignore_special_character != body2.anime_search_filter.ignore_special_character
        || body.anime_search_filter.partial_match != body2.anime_search_filter.partial_match
        || body.anime_search_filter.case_sensitive != body2.anime_search_filter.case_sensitive)) {
      return false
    }

    // if the artist filters are different
    if (body.artist_search_filter && body2.artist_search_filter
      && (body.artist_search_filter.search != body2.artist_search_filter.search
        || body.artist_search_filter.ignore_special_character != body2.artist_search_filter.ignore_special_character
        || body.artist_search_filter.partial_match != body2.artist_search_filter.partial_match
        || body.artist_search_filter.case_sensitive != body2.artist_search_filter.case_sensitive
        || body.artist_search_filter.group_granularity != body2.artist_search_filter.group_granularity
        || body.artist_search_filter.max_other_artist != body2.artist_search_filter.max_other_artist)) {
      return false
    }

    // if the song name filters are different
    if (body.song_name_search_filter && body2.song_name_search_filter
      && (body.song_name_search_filter.search != body2.song_name_search_filter.search
        || body.song_name_search_filter.ignore_special_character != body2.song_name_search_filter.ignore_special_character
        || body.song_name_search_filter.partial_match != body2.song_name_search_filter.partial_match
        || body.song_name_search_filter.case_sensitive != body2.song_name_search_filter.case_sensitive)) {
      return false
    }

    // if the composer filters are different
    if (body.composer_search_filter && body2.composer_search_filter
      && (body.composer_search_filter.search != body2.composer_search_filter.search
        || body.composer_search_filter.ignore_special_character != body2.composer_search_filter.ignore_special_character
        || body.composer_search_filter.partial_match != body2.composer_search_filter.partial_match
        || body.composer_search_filter.case_sensitive != body2.composer_search_filter.case_sensitive
        || body.composer_search_filter.arrangement != body2.composer_search_filter.arrangement)) {
      return false
    }

    return true
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

    if (this.areBodyIdenticalBaseSearch(body, this.previousBody)) {
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

    if (!this.showAdvancedFilters) {
      this.downloadFileName = this.mainFilter.replace(" ", "") + "_SongList.json"
    }
    else {
      this.downloadFileName = this.animeFilter.replace(" ", "") + "_" + this.songNameFilter.replace(" ", "") + "_" + this.artistFilter.replace(" ", "") + "_" + this.composerFilter.replace(" ", "") + "_SongList.json"
      this.downloadFileName = this.downloadFileName.replace("__", "")
    }
    let theJSON = JSON.stringify(this.currentSongList);
    let blob = new Blob([theJSON], { type: 'text/json' });
    let url = window.URL.createObjectURL(blob);
    let uri: SafeUrl = this.sanitizer.bypassSecurityTrustUrl(url);
    this.downloadJsonHref = uri;
  }


}
