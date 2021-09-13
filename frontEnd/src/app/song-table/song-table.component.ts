import { Component, Input, Output, EventEmitter } from '@angular/core';

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

  @Input() songTable: any

  ngOnChanges(changes: Event) {
    this.ascendingOrder = false;
    this.sortFunction("annId");
  }


  lastColName: string = ""
  ascendingOrder: boolean = false;
  showSongInfoPopup: boolean = false;
  doubleClickPreventer: boolean = false;

  popUpannURL: string = "";
  popUpAnime: string = "";
  popUpHDLink: string = "";
  popUpMDLink: string = "";
  popUpAudioLink: string = "";
  popUpArtistsInfo = [];

  tableHeaders = ["annId", "Anime", "Type", "Song Name", "Artist"];

  sortFunction(colName: string) {

    if (!this.songTable) {
      return;
    }


    if (colName == "Song Name") {
      colName = "SongName"
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
      let comparison = this.compareSongType(a["Type"], b["Type"])
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
          return this.compareSongType(a["Type"], b["Type"]);
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
    this.popUpAnime = song.Anime;
    this.popUpHDLink = song.sept;
    this.popUpMDLink = song.quatre;
    this.popUpAudioLink = song.mptrois;
    this.popUpArtistsInfo = song.artists;
    this.showSongInfoPopup = !this.showSongInfoPopup;
    this.doubleClickPreventer = true;
  }

  @Output() mp3PlayerClicked = new EventEmitter();

  playMP3music(song: any) {
    this.mp3PlayerClicked.emit(song.mptrois)
  }


}
