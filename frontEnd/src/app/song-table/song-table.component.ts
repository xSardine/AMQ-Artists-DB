import { Component, Input, Output, EventEmitter } from '@angular/core';
import { SearchRequestService } from '../core/services/search-request.service';
import { MatomoTracker } from '@ngx-matomo/tracker';

@Component({
  selector: 'app-song-table',
  templateUrl: './song-table.component.html',
  styleUrls: ['./song-table.component.css'],
  host: {
    '(document:click)': 'onAnyClick($event)',
  },
  template: `
       {{ message }}
  `,
})
export class SongTableComponent {

  constructor(private searchRequestService: SearchRequestService, private matomoTracker: MatomoTracker) {
  }

  @Input() songTable: any

  ngOnChanges(changes: Event) {
    if (this.checkRankedTime()) {
      this.rankedTime = true
    }
    else {
      this.rankedTime = false
    }
    this.ascendingOrder = false;
    this.sortFunction("annId");
  }


  lastColName: string = ""
  ascendingOrder: boolean = false;
  showSongInfoPopup: boolean = false;
  doubleClickPreventer: boolean = false;
  animeJPName: string = ""

  popUpannId: string = "";
  popUpVintage: string = "";
  popUpAnimeType: string = "";
  popUpannSongId: string = "";
  popUpSongName: string = "";
  popUpArtist: string = "";
  popUpSongDiff: string = "";
  popUpannURL: string = "";
  popUpAnime: string = "";
  popUpHDLink: string = "";
  popUpMDLink: string = "";
  popUpAudioLink: string = "";
  popUpArtistsInfo = [];
  popUpComposersInfo = [];
  popUpArrangersInfo = [];


  tableHeaders = ["annId", "Anime", "Type", "Song Name", "Artist"];

  rankedTime = false;
  RankedDisabledTimeLeft = 0

  checkRankedTime() {
    let date = new Date()
    let hour = date.getUTCHours()
    let minute = date.getUTCMinutes()

    // 20:30 CST   -> 20:30 CET      -> 20:30 JST (all converted to UTC)
    // West Ranked -> Central Ranked -> East Ranked first half
    if ((hour == 1 && minute >= 30) || (hour == 18 && minute >= 30) || (hour == 11 && minute >= 30)) {
      this.RankedDisabledTimeLeft = 90 - minute
      return true
    }
    // 21:30 CST   -> 21:30 CET      -> 21:30 JST (all converted to UTC)
    // West Ranked -> Central Ranked -> East Ranked second half
    else if ((hour == 2 && minute < 30) || (hour == 19 && minute < 30) || (hour == 12 && minute < 30)) {
      this.RankedDisabledTimeLeft = 30 - minute
      return true
    }
    return false

  }

  copyToClipboard(copytext: string) {
    navigator.clipboard.writeText(copytext);
    return;
  }


  sortFunction(colName: string) {

    if (!this.songTable) {
      return;
    }


    if (colName == "Song Name") {
      colName = "songName"
    }

    if (this.lastColName != colName) {
      this.ascendingOrder = false;
      this.lastColName = colName;
    }

    this.songTable.sort((a: any, b: any) => this.compareTwoSong(colName, a, b))
    this.lastColName = colName
    this.ascendingOrder = !this.ascendingOrder

  }

  compareTwoSong(colName: string, a: any, b: any) {

    if (colName == "Type") {
      let comparison = this.compareSongType(a["songType"], b["songType"])
      if (comparison == 1) {
        return this.ascendingOrder ? -1 : 1;
      }
      else if (comparison == -1) {
        return this.ascendingOrder ? 1 : -1;
      }
      else {

        if (a["annId"] < b["annId"]) {
          return -1;
        }
        else if (a["annId"] > b["annId"]) {
          return 1;
        }
        else {
          return 0
        }
      }
    }
    else {
      if (a[colName] < b[colName]) {
        return this.ascendingOrder ? 1 : -1;
      }
      else if (a[colName] > b[colName]) {
        return this.ascendingOrder ? -1 : 1;
      }
      else {
        if (colName == "annId" || colName == "Anime") {
          return this.compareSongType(a["songType"], b["songType"]);
        }
        else {
          if (a["annId"] < b["annId"]) {
            return -1;
          }
          else if (a["annId"] > b["annId"]) {
            return 1;
          }
          else {
            return 0
          }
        }
      }
    }
  }


  compareSongType(type1: any, type2: any) {

    let number1 = parseInt(type1.match(/^\s*(\S+)\s*(.*?)\s*$/).slice(1)[1])
    let string1 = type1.match(/^\s*(\S+)\s*(.*?)\s*$/).slice(1)[0]
    let number2 = parseInt(type2.match(/^\s*(\S+)\s*(.*?)\s*$/).slice(1)[1])
    let string2 = type2.match(/^\s*(\S+)\s*(.*?)\s*$/).slice(1)[0]

    switch (string1) {
      case "Ending":
        string1 = 1;
        break;
      case "Insert":
        string1 = 2;
        break;
      case "Opening":
        string1 = 0;
        break;
    }

    switch (string2) {
      case "Ending":
        string2 = 1;
        break;
      case "Insert":
        string2 = 2;
        break;
      case "Opening":
        string2 = 0;
        break;
    }

    if (string1 < string2) {
      return -1
    }
    else if (string1 > string2) {
      return 1
    }
    else if (number1 < number2) {
      return -1
    }
    else if (number1 > number2) {
      return 1
    }
    else {
      return 0
    }
  }


  onAnyClick() {
    if (this.showSongInfoPopup && !this.doubleClickPreventer) {
      this.showSongInfoPopup = !this.showSongInfoPopup;
    }
    else if (this.showSongInfoPopup) {
      this.doubleClickPreventer = !this.doubleClickPreventer;
    }
  }

  displaySongIngoPopup(song: any) {
    this.popUpannURL = "https://www.animenewsnetwork.com/encyclopedia/anime.php?id=" + song.annId;
    this.popUpannId = song.annId;
    this.popUpVintage = song.animeVintage;
    this.popUpAnimeType = song.animeType;
    this.popUpannSongId = song.annSongId;
    this.popUpAnime = song.animeExpandName;
    this.popUpSongName = song.songName;
    this.popUpArtist = song.artist;
    this.popUpSongDiff = song.songDifficulty;
    this.popUpHDLink = song.sept;
    this.popUpMDLink = song.quatre;
    this.popUpAudioLink = song.mptrois;
    this.popUpArtistsInfo = song.artists;
    this.popUpComposersInfo = song.composers;
    this.popUpArrangersInfo = song.arrangers;
    this.showSongInfoPopup = !this.showSongInfoPopup;
    this.doubleClickPreventer = true;
    this.animeJPName = song.animeJPName
  }

  removeItemsById(arr: any, id: any) {
    var i = arr.length;
    if (i) {   // (not 0)
      while (--i + 1) {
        if (i == id) {
          arr.splice(i, 1);
        }
      }
    }
  }

  getIndexbyElement(arr: any, element: any) {

    let index = 0

    for (let el in arr) {
      if (element == arr[el]) {
        return index
      }
      index += 1
    }
    return -1

  }

  @Output() mp3PlayerClicked = new EventEmitter();

  playMP3music(song: any) {
    this.mp3PlayerClicked.emit(song)
  }

  deleteRowEntry(song: any) {
    let id = this.getIndexbyElement(this.songTable, song)
    this.removeItemsById(this.songTable, id);
  }

  @Output() sendSongListtoTable = new EventEmitter();

  sendMessage(currentSongList: any) {
    this.sendSongListtoTable.emit(currentSongList)
  }

  searchArtistId(artists: any) {

    let id_arr = []
    let tmpstr = ""
    for (let artist in artists) {
      id_arr.push(artists[artist].id)
      tmpstr += artists[artist].id + "-"
    }
    tmpstr = tmpstr.substring(0, tmpstr.length - 1)

    let body = {
      "artist_ids": id_arr,
      "group_granularity": 0,
      "max_other_artist": 99,
      "ignore_duplicate": false,
      "opening_filter": true,
      "ending_filter": true,
      "insert_filter": true,
    }

    this.matomoTracker.trackEvent('SearchCall', 'ArtistID', tmpstr);

    let currentSongList
    currentSongList = this.searchRequestService.artistIdsSearchRequest(body).subscribe(data => {
      currentSongList = data
      this.sendMessage(currentSongList)
    });
  }

  searchPopUpArtist(artist: any) {

    let body = {
      "artist_ids": [artist.id],
      "group_granularity": 0,
      "max_other_artist": 99,
      "ignore_duplicate": false,
      "opening_filter": true,
      "ending_filter": true,
      "insert_filter": true,
    }

    this.matomoTracker.trackEvent('SearchCall', 'ArtistID', artist.id);

    let currentSongList
    currentSongList = this.searchRequestService.artistIdsSearchRequest(body).subscribe(data => {
      currentSongList = data
      this.sendMessage(currentSongList)
      this.showSongInfoPopup = false
    });

  }

  searchAnnId(id: any) {

    let body = {
      "annId": id,
      "ignore_duplicate": false,
      "opening_filter": true,
      "ending_filter": true,
      "insert_filter": true,
    }

    this.matomoTracker.trackEvent('SearchCall', 'annID', id);

    let currentSongList
    currentSongList = this.searchRequestService.annIdSearchRequest(body).subscribe(data => {
      currentSongList = data
      this.sendMessage(currentSongList)
    });
  }

}