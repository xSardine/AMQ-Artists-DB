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

  animeTitleLang: string = "JP"
  composerDisplay: boolean = true

  private readonly volumeKey = 'vimePlayerVolume'; 
  private volumeChangeListener!: (event: Event) => void;
  
  ngAfterViewInit() {
    const playerElement = this.player.getElement(); 
    const savedVolume = localStorage.getItem(this.volumeKey);
    
    this.player.volume = savedVolume ? parseFloat(savedVolume) : 0.5;
  
    this.volumeChangeListener = () => {
      localStorage.setItem(this.volumeKey, this.player.volume.toString());
    };
  
    playerElement.addEventListener('volumechange', this.volumeChangeListener);
  }
  
  ngOnDestroy() {
    const playerElement = this.player.getElement();
    playerElement.removeEventListener('volumechange', this.volumeChangeListener);
  }

  receiveSongList($event: any) {
    this.songList = $event
  }

  receivePreviousBody($event: any) {
    this.previousBody = $event
  }

  playMP3(song: any) {
    this.url = null;
    setTimeout(() => { this.url = "https://naedist.animemusicquiz.com/" + song.audio; this.currentlyPlayingArtist = song.songArtist; this.currentlyPlayingSongName = song.songName; }, 0)
  }

  toggleAnimeLang() {
    this.animeTitleLang = (this.animeTitleLang == "JP") ? "EN" : "JP"
  }

  toggleComposerDisplay() {
    this.composerDisplay = !this.composerDisplay
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

}
