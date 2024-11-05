import { Component, ViewChild, AfterViewInit, ElementRef } from '@angular/core';
import { MediaPlayer, LocalMediaStorage } from 'vidstack';

class CustomLocalMediaStorage extends LocalMediaStorage {
  // Override to prevent automatic timestamp retrieval
  async getTime(): Promise<number | null> {
    return null; // Return null to opt-out of retrieving the current time
  }

  // Override to prevent automatic timestamp saving
  async setTime(_time: number, _ended: boolean): Promise<void> {
    // Do nothing
  }
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements AfterViewInit {
  @ViewChild('playerRef', { static: false }) playerRef!: ElementRef; // Reference to the media player
  player: MediaPlayer = this.playerRef?.nativeElement; // Media player instance
  customLocalMediaStorage = new CustomLocalMediaStorage();

  title = 'anisongDB';
  url: any = '';
  songList: any;
  previousBody: any;
  currentlyPlayingArtist: any = '';
  currentlyPlayingSongName: any = '';
  animeTitleLang: string = 'JP';
  composerDisplay: boolean = true;

  // Keys for storing player preferences in localStorage
  private readonly volumeKey = 'vimePlayerVolume';
  private readonly langKey = 'animeTitleLang';
  private readonly composerKey = 'composerDisplay';

  receiveSongList($event: any) {
    this.songList = $event;
  }

  receivePreviousBody($event: any) {
    this.previousBody = $event;
  }

  ngOnInit() {
    this.initializeTableSettings();
  }

  private initializeTableSettings() {
    const savedLang = localStorage.getItem(this.langKey);
    this.animeTitleLang = savedLang ? savedLang : 'JP';

    const savedComposerDisplay = localStorage.getItem(this.composerKey);
    this.composerDisplay =
      savedComposerDisplay !== null ? savedComposerDisplay === 'true' : true;
  }

  private playerSettingsToInitialize() {
    const savedVolume = localStorage.getItem(this.volumeKey);
    if (this.player) {
      (this.player as any).volume = savedVolume ? parseFloat(savedVolume) : 0.5; // Ensure correct type casting
    }
  }

  toggleAnimeLang() {
    this.animeTitleLang = this.animeTitleLang === 'JP' ? 'EN' : 'JP';
    localStorage.setItem(this.langKey, this.animeTitleLang);
  }

  toggleComposerDisplay() {
    this.composerDisplay = !this.composerDisplay;
    localStorage.setItem(this.composerKey, this.composerDisplay.toString());
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

  ngAfterViewInit() {
    // Ensure player is defined before calling methods
    if (this.playerRef) {
      this.player = this.playerRef.nativeElement;
      this.player.startLoading();
    } else {
      console.error('Player is not defined in ngAfterViewInit');
    }
  }

  private waitForCanPlay(player: MediaPlayer): Promise<void> {
    return new Promise((resolve, reject) => {
      const handleCanPlay = () => {
        resolve();
        player.removeEventListener('can-play', handleCanPlay); // Cleanup
      };

      const handleError = (event: Event) => {
        reject(event);
        player.removeEventListener('can-play', handleCanPlay); // Cleanup on error
      };

      player.addEventListener('can-play', handleCanPlay);
      player.addEventListener('error', handleError);
    });
  }

  async playMP3(song: any) {
    const { player } = this;

    try {
      await this.setUrl(song);
      await this.initializePlayerSettings();

      // Wait for the player to be ready
      await this.waitForCanPlay(player);

      // Start playing the media
      await player?.play();
    } catch (error) {
      console.error('Error playing song:', error);
    }
  }

  private setUrl(song: any): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        // Construct the full URL for the MP3 file
        const songUrl = 'https://naedist.animemusicquiz.com/' + song.audio;

        // This set variables so that the song name and artist can be displayed on the player <div>
        this.currentlyPlayingArtist = song.songArtist;
        this.currentlyPlayingSongName = song.songName;

        // Set the source URL for the media player
        (this.player as any).src = songUrl; // Set the src attribute

        resolve();
      }, 0);
    });
  }
}
