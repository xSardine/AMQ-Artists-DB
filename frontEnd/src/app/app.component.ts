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
    standalone: false
})
export class AppComponent implements AfterViewInit {
  @ViewChild('audioPlayerRef', { static: false }) audioPlayerRef!: ElementRef;
  audioPlayer: MediaPlayer = this.audioPlayerRef?.nativeElement;
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

  toggleAnimeLang() {
    this.animeTitleLang = this.animeTitleLang === 'JP' ? 'EN' : 'JP';
    localStorage.setItem(this.langKey, this.animeTitleLang);
  }

  toggleComposerDisplay() {
    this.composerDisplay = !this.composerDisplay;
    localStorage.setItem(this.composerKey, this.composerDisplay.toString());
  }

  ngAfterViewInit() {
    // Ensure player is defined before calling methods
    if (this.audioPlayerRef) {
      this.audioPlayer = this.audioPlayerRef.nativeElement;
      (this.audioPlayer as any).crossOrigin = true;
      (this.audioPlayer as any).keyTarget = 'document';
      this.audioPlayer.startLoading();
    } else {
      console.error('Player is not defined in ngAfterViewInit');
    }
  }

  private waitForCanPlay(player: MediaPlayer): Promise<void> {
    return new Promise((resolve, reject) => {
      const handleCanPlay = () => {
        resolve();
        player.removeEventListener('can-play', handleCanPlay);
      };

      const handleError = (event: Event) => {
        reject(event);
        player.removeEventListener('can-play', handleCanPlay);
      };

      player.addEventListener('can-play', handleCanPlay);
      player.addEventListener('error', handleError);
    });
  }

  async playMP3(song: any) {
    const { audioPlayer } = this;

    try {
      await this.setUrl(audioPlayer, song);

      // Wait for the player to be ready
      await this.waitForCanPlay(audioPlayer);

      // Start playing the media
      await audioPlayer?.play();
    } catch (error) {
      console.error('Error playing song:', error);
    }
  }

  private setUrl(player: MediaPlayer, song: any): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        // Construct the full URL for the MP3 file

        const songUrl = `https://naedist.animemusicquiz.com/${song.audio}`;

        // This set variables so that the song name and artist can be displayed on the player <div>
        this.currentlyPlayingArtist = song.songArtist;
        this.currentlyPlayingSongName = song.songName;

        // Set the source URL for the media player
        (player as any).src = songUrl; // Set the src attribute
        player.title = song.songName + ' by ' + song.songArtist;

        resolve();
      }, 0);
    });
  }
}
