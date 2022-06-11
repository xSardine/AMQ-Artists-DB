import { Component, ViewChild } from '@angular/core';
import { Player } from '@vime/angular';
import { ThemeService } from "./core/services/theme.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {

  constructor(private themeService: ThemeService) { }

  title = 'anisongDB';

  @ViewChild('player') player!: Player;
  url: any = "";

  songList: any;
  previousBody: any;

  currentlyPlayingArtist: any = ""
  currentlyPlayingSongName: any = ""

  receiveSongList($event: any) {
    this.songList = $event
  }

  receivePreviousBody($event: any) {
    this.previousBody = $event
  }

  playMP3(song: any) {
    this.url = null
    setTimeout(() => { this.url = song.audio; this.currentlyPlayingArtist = song.songArtist; this.currentlyPlayingSongName = song.songName }, 0)
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

}
