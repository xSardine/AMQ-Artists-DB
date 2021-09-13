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

  title = 'artistDB';

  @ViewChild('player') player!: Player;
  url: any = "";

  songList: any;

  receiveSongList($event: any) {
    this.songList = $event
  }

  playMP3(mp3Link: string) {
    this.url = null
    setTimeout(() => { this.url = mp3Link; }, 0)
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

}
