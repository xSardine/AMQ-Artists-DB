import { Component, ViewChild } from '@angular/core';
import { ThemeService } from "./core/services/theme.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {

  constructor(private themeService: ThemeService) { }

  title = 'anisongDB';

  @ViewChild('player') player: any;
  url: any = "";

  songList: any;
  previousBody: any;

  currentlyPlayingArtist: any = ""
  currentlyPlayingSongName: any = ""

  animeTitleLang: string = "JP"
  composerDisplay: boolean = true

  // Keys for storing player preferences in localStorage
  private readonly volumeKey = 'vimePlayerVolume';
  private readonly langKey = 'animeTitleLang';
  private readonly composerKey = 'composerDisplay';

  receiveSongList($event: any) {
    this.songList = $event
  }

  receivePreviousBody($event: any) {
    this.previousBody = $event
  }

  ngOnInit() {
    this.initializeTableSettings()
  }

  private initializeTableSettings() {
    const savedLang = localStorage.getItem(this.langKey);
    this.animeTitleLang = savedLang ? savedLang : "JP";

    const savedComposerDisplay = localStorage.getItem(this.composerKey);
    this.composerDisplay = savedComposerDisplay !== null ? savedComposerDisplay === 'true' : true;
  }

  private playerSettingsToInitialize() {
    const savedVolume = localStorage.getItem(this.volumeKey);
    this.player.volume = savedVolume ? parseFloat(savedVolume) : 0.5;
  }

  private initializePlayerSettings(): Promise<void> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (this.player) {
          this.playerSettingsToInitialize(); // Initialize player settings if player is populated
          resolve();
        } else {
          reject('Player not ready');
        }
      }, 0);
    });
  }

  private setUrl(song: any): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.url = "https://naedist.animemusicquiz.com/" + song.audio;
        this.currentlyPlayingArtist = song.songArtist;
        this.currentlyPlayingSongName = song.songName;
        resolve();
      }, 0);
    });
  }

  async playMP3(song: any) {
    this.url = null;
    try {
      await this.setUrl(song);
      await this.initializePlayerSettings(); // After player is populated, initialize settings/volume
    } catch (err) {
      console.error('Error playing song:', err)
    }
  }

  toggleAnimeLang() {
    this.animeTitleLang = (this.animeTitleLang === "JP") ? "EN" : "JP";
    localStorage.setItem(this.langKey, this.animeTitleLang);
  }

  toggleComposerDisplay() {
    this.composerDisplay = !this.composerDisplay;
    localStorage.setItem(this.composerKey, this.composerDisplay.toString());
  }

  handleVmVolumeChange(volumeEvent: CustomEvent<number>) {
    const newVolume: number = volumeEvent.detail
    this.player.volume = newVolume
    localStorage.setItem(this.volumeKey, newVolume.toString())
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

}
