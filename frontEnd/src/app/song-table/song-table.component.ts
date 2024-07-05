import { Component, Input, Output, EventEmitter } from '@angular/core';
import { SearchRequestService } from '../core/services/search-request.service';

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

  constructor(private searchRequestService: SearchRequestService) {
  }

  @Input() songTable: any
  @Input() previousBody: any
  @Input() animeTitleLang: any

  @Output() mp3PlayerClicked = new EventEmitter();
  playMP3music(song: any) {
    this.currentPlayingSong = song
    this.mp3PlayerClicked.emit(song)
  }

  @Output() sendSongListtoTable = new EventEmitter();
  sendSongList(currentSongList: any) {
    this.sendSongListtoTable.emit(currentSongList)
  }

  @Output() sendPreviousBody = new EventEmitter();
  sendPrevBody(body: any) {
    this.sendPreviousBody.emit(body)
  }

  ngOnChanges(changes: Event) {
    this.rankedTime = this.checkRankedTime()
    this.ascendingOrder = false;
    this.currentAverage = this.computeAverage(this.songTable)
    this.sortFunction("annId");
  }

  isCurrentPlayingSong(song: any) {
    return song === this.currentPlayingSong
  }

  maxGridNb: number = 3

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
  popUpSongCat: string = "";
  popUpannURL: string = "";
  popUpAnime: string = "";
  popUpHDLink: string = "";
  popUpMDLink: string = "";
  popUpAudioLink: string = "";
  popUpArtistsInfo: any = [];
  popUpComposersInfo: any = [];
  popUpArrangersInfo: any = [];
  currentAverage: any
  gridStyle: any
  subGridStyle: any
  clipboardPopUpStyle: any
  show: boolean = false

  tableHeaders = ["annId", "Anime", "Type", "Song Name", "Artist"];

  rankedTime = false;
  RankedDisabledTimeLeft = 0
  currentPlayingSong: any

  checkRankedTime() {
    // Define the ranked time intervals as an array of objects
    let rankedTimeIntervals = [
      // CST NA
      {
        start: new Date().setUTCHours(1, 30, 0, 0),
        end: new Date().setUTCHours(2, 23, 0, 0)
      },
      // JST Asia
      {
        start: new Date().setUTCHours(11, 30, 0, 0),
        end: new Date().setUTCHours(12, 23, 0, 0)
      },
      // CET EU
      {
        start: new Date().setUTCHours(18, 30, 0, 0),
        end: new Date().setUTCHours(19, 23, 0, 0)
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



  copyToClipboard(event: any, copytext: string) {
    navigator.clipboard.writeText(copytext);
    this.clipboardPopUpStyle = { "left": event.pageX + 10 + "px", "top": event.pageY - 20 + "px" }
    this.show = true;
    setTimeout(() => { this.show = false }, 400);
    return;
  }


  computeAverage(array: any[]): number {

    if (array === undefined) {
      return 0;
    }

    const diffs = array.filter(song => song.songDifficulty).map(song => song.songDifficulty);

    const total = diffs.reduce((sum, item) => sum + item, 0);

    return +(total / diffs.length).toFixed(1);
  }


  sortArtists(artists: { names: string[], groups: string[], members: string[] }[]) {
    // Create a new, sorted array of artists
    const sortedArtists = artists.map(artist => artist)
      .sort((a, b) => {
        // Use the optional chaining operator to safely access the group and member lengths
        // If either property is missing, the length will be treated as -1 (to compensate with title header)
        // for names specifically, 0 and 1 will be treated as -1 as well
        let aLength = ((a.names?.length ?? -1) <= 1 ? -1 : (a.names?.length ?? -1)) + (a.groups?.length ?? -1) + (a.members?.length ?? -1);
        let bLength = ((b.names?.length ?? -1) <= 1 ? -1 : (b.names?.length ?? -1)) + (b.groups?.length ?? -1) + (b.members?.length ?? -1);

        // Sort the artists based on their group and member lengths
        return aLength - bLength;
      });

    // Return the sorted array
    return sortedArtists;
  }


  getTypeAndNumber(songType: string) {

    const words = songType.split(" ");
    const type = words[0];
    const number = parseInt(words[1]) ? parseInt(words[1]) : 0;

    return { type, number };
  }

  compareSongsType(songType1: string, songType2: string) {

    const type1 = this.getTypeAndNumber(songType1);
    const type2 = this.getTypeAndNumber(songType2);

    // Create an object to map the song type to a sortable value
    const songTypes = ["Opening", "Ending", "Insert"];

    // Compare the song types first, and if they are equal, compare the numbers
    return -(songTypes.indexOf(type1.type) - songTypes.indexOf(type2.type) || type1.number - type2.number);
  }


  compareTwoSongs(colName: string, a: any, b: any) {

    let comparison;

    // Compare values of song type if colName is songType
    if (colName === "Type") {
      comparison = this.compareSongsType(a["songType"], b["songType"]);
      // else compare value of given column
    } else {
      comparison = a[colName] < b[colName] ? 1 : (a[colName] > b[colName] ? -1 : 0);
    }

    // If we sort on annId the songs have the same annId, compare songType
    if (comparison === 0 && colName === "annId") {
      comparison = this.compareSongsType(a["songType"], b["songType"]);
    }

    // Else if we sort on anything else, and they have the same value, compare on annId
    else if (comparison === 0) {
      comparison = a["annId"] > b["annId"] ? -1 : (a["annId"] < b["annId"] ? 1 : 0);
    }

    return this.ascendingOrder ? comparison : -comparison;

  }

  sortFunction(colName: string) {

    if (!this.songTable) {
      return;
    }

    const colNamesMap: Record<string, string> = {
      "Song Name": "songName",
      "Artist": "songArtist",
      "Anime": this.animeTitleLang == "JP" ? "animeJPName" : "animeENName"
    };

    const sortColName = colNamesMap[colName] || colName;

    this.songTable.sort((a: any, b: any) => this.compareTwoSongs(sortColName, a, b))

    // update the lastColName and ascendingOrder properties
    if (this.lastColName !== colName) {
      this.lastColName = colName;
      this.ascendingOrder = true;
    } else {
      this.ascendingOrder = !this.ascendingOrder;
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
    this.popUpannSongId = song.annSongId != -1 ? song.annSongId : null;
    this.popUpAnime = this.animeTitleLang == "JP" ? song.animeJPName : song.animeENName;
    this.popUpSongName = song.songName;
    this.popUpArtist = song.songArtist;
    this.popUpSongDiff = song.songDifficulty;
    this.popUpSongCat = song.songCategory;
    this.popUpHDLink = song.HQ;
    this.popUpMDLink = song.MQ;
    this.popUpAudioLink = song.audio;
    this.popUpArtistsInfo = this.sortArtists(song.artists);
    this.popUpComposersInfo = song.composers;
    this.popUpArrangersInfo = song.arrangers;
    this.showSongInfoPopup = !this.showSongInfoPopup;
    this.doubleClickPreventer = true;
    this.animeJPName = song.animeJPName
    this.gridStyle = {
      "grid-template-columns": `repeat(${Math.min(this.maxGridNb, this.popUpArtistsInfo.length)}, 1fr)`
    }
    this.subGridStyle = {
      "grid-template-columns": `repeat(${this.maxGridNb - Math.min(this.maxGridNb, this.popUpArtistsInfo.length) + 1}, 1fr)`
    }

  }

  deleteRowEntry(song: any) {
    const id = this.songTable.findIndex((obj: any) => obj === song)
    this.songTable.splice(id, 1);
    this.currentAverage = this.computeAverage(this.songTable)
  }

  searchArtistIds(artists: any) {


    let id_arr
    if (artists.id) {
      id_arr = [artists.id]
    }
    else {
      id_arr = []
      for (let artist in artists) {
        id_arr.push(artists[artist].id)
      }
    }

    let body = {
      "artist_ids": id_arr,
      "group_granularity": 0,
      "max_other_artist": 99,
      "ignore_duplicate": false,
      "opening_filter": true,
      "ending_filter": true,
      "insert_filter": true,
    }

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return
    }

    this.previousBody = body
    this.sendPrevBody(body)

    let currentSongList
    currentSongList = this.searchRequestService.artistIdsSearchRequest(body).subscribe(data => {
      currentSongList = data
      this.sendSongList(currentSongList)
    });
  }

  searchComposerIds(composers: any) {

    let id_arr
    if (composers.id) {
      id_arr = [composers.id]
    }
    else {
      id_arr = []
      for (let composer in composers) {
        id_arr.push(composers[composer].id)
      }
    }

    let body = {
      "composer_ids": id_arr,
      "arrangement": true,
      "ignore_duplicate": false,
      "opening_filter": true,
      "ending_filter": true,
      "insert_filter": true,
    }

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return
    }

    this.previousBody = body
    this.sendPrevBody(body)

    let currentSongList
    currentSongList = this.searchRequestService.composerIdsSearchRequest(body).subscribe(data => {
      currentSongList = data
      this.sendSongList(currentSongList)
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

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return
    }

    this.previousBody = body
    this.sendPrevBody(body)

    let currentSongList
    currentSongList = this.searchRequestService.annIdSearchRequest(body).subscribe(data => {
      currentSongList = data
      this.sendSongList(currentSongList)
    });

  }

}
