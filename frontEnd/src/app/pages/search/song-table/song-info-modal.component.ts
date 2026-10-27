import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  computed,
  ElementRef,
  inject,
  input,
  viewChild,
} from '@angular/core';
import { ClipboardPopupOutletComponent } from '../../../shared/feedback/clipboard-popup-outlet.component';
import { InfoPopoverComponent } from '../../../shared/controls/info-popover.component';
import { hasAnnSongId, hasSongPlaybackSource, SongCredit, Song } from '../songs/song';
import { formatSongLength, getBroadcastMetadata } from '../songs/song-metadata';
import { AudioPlaybackService } from '../audio/audio-playback.service';
import { ClipboardService } from '../../../shared/feedback/clipboard.service';
import { SearchModalService } from '../search-modal.service';
import { RankedStatusService } from '../ranked-status.service';
import { SearchPreferencesService } from '../settings/search-preferences.service';
import { SearchService } from '../query/search.service';
import { ModalShellComponent } from '../../../shared/dialogs/modal-shell.component';
import { SongWorkspaceStore } from '../songs/song-workspace.store';
import { buildCreditSections, collectPersonIds, CreditSearchRole, creditSearchTitle } from './song-credits';
import { ANIME_LIST_SITES, SONG_DIST_LINKS } from './song-links';

@Component({
  selector: 'app-song-info-modal',
  templateUrl: './song-info-modal.component.html',
  styleUrls: ['./song-info-modal.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(keydown)': 'onKeydown($event)' },
  imports: [ClipboardPopupOutletComponent, InfoPopoverComponent, ModalShellComponent],
})
export class SongInfoModalComponent {
  private readonly searches = inject(SearchService);
  private readonly playback = inject(AudioPlaybackService);
  readonly clipboard = inject(ClipboardService);
  private readonly rankedStatusService = inject(RankedStatusService);
  private readonly modals = inject(SearchModalService);
  readonly preferences = inject(SearchPreferencesService);
  private readonly workspace = inject(SongWorkspaceStore);

  readonly song = input.required<Song>();
  readonly modalContent = viewChild<ElementRef<HTMLElement>>('modalContent');

  readonly rankedActive = this.rankedStatusService.active;
  readonly rowIndex = computed(() => this.workspace.songs()?.indexOf(this.song()) ?? -1);
  readonly totalRows = computed(() => this.workspace.songs()?.length ?? 0);
  readonly canNavigate = computed(() => this.rowIndex() >= 0 && this.totalRows() > 1);
  readonly showSongIds = computed(() => this.preferences.preferences().showSongIds);
  readonly showArtistIds = computed(() => this.preferences.preferences().showArtistIds);
  readonly songAndArtist = computed(() => {
    const song = this.song();
    return `"${song.songName}" by ${song.songArtist || 'Unknown Artist'}`;
  });
  readonly creditSearchTitle = creditSearchTitle;

  readonly animeTitles = computed(() => {
    const song = this.song();
    const localized = [song.animeENName, song.animeJPName];
    if (this.preferences.preferences().animeTitleLanguage === 'JP') localized.reverse();
    const names = [...localized, ...song.animeAltName].map(name => name.trim()).filter(Boolean);
    const [primary = '–', ...secondary] = [...new Set(names)];
    return { primary, secondary };
  });
  readonly creditSections = computed(() => buildCreditSections(this.song()));
  readonly broadcast = computed(() => getBroadcastMetadata(this.song()).label);
  readonly formattedLength = computed(() => formatSongLength(this.song().songLength));
  readonly annSongId = computed(() => {
    const song = this.song();
    return hasAnnSongId(song) ? song.annSongId : null;
  });
  readonly animeListSites = ANIME_LIST_SITES;
  readonly songDistLinks = SONG_DIST_LINKS;
  readonly canPlay = computed(() => hasSongPlaybackSource(this.song()));
  readonly playbackActive = computed(() => {
    const state = this.playback.state();
    return (state.status === 'playing' || state.status === 'loading')
      && state.song.annSongId === this.song().annSongId;
  });

  private readonly maxGridColumns = 3;

  constructor() {
    // Scroll back to the top after each rendered song change.
    afterRenderEffect(() => {
      this.song();
      this.modalContent()?.nativeElement.scrollTo(0, 0);
    });
  }

  onCopy(event: MouseEvent, text: unknown) {
    this.clipboard.copy(event, text);
  }

  onKeydown(event: KeyboardEvent) {
    if (event.defaultPrevented || event.isComposing
      || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const target = event.target;
    if (target instanceof HTMLElement
      && (target.isContentEditable || target.closest('input, textarea, select'))) return;
    if (window.getSelection()?.isCollapsed === false) return;

    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      event.stopPropagation();
      this.navigate(event.key === 'ArrowLeft' ? -1 : 1);
    }
  }

  togglePlayback(): void {
    if (this.playbackActive()) {
      this.playback.pause();
    } else if (this.canPlay()) {
      this.playback.play(this.song());
    }
  }

  gridColumns(itemCount: number): string {
    return `repeat(${Math.min(this.maxGridColumns, itemCount)}, minmax(0, 1fr))`;
  }

  creditSubgridColumns(sectionPeopleCount: number): string {
    const parentColumns = Math.min(this.maxGridColumns, sectionPeopleCount);
    return `repeat(${this.maxGridColumns - parentColumns + 1}, minmax(0, 1fr))`;
  }

  close(): void {
    this.modals.close('song-info');
  }

  navigate(delta: number): void {
    const songs = this.workspace.songs();
    const index = songs?.indexOf(this.song()) ?? -1;
    if (!songs || songs.length <= 1 || index < 0) return;

    this.modals.open({
      type: 'song-info',
      song: songs[(index + delta + songs.length) % songs.length],
    });
  }

  searchCredit(person: SongCredit, role: CreditSearchRole, event?: MouseEvent) {
    event?.stopPropagation();
    const personIds = collectPersonIds(person);
    const searchStarted = role === 'artist'
      ? this.searches.searchArtistIds(personIds)
      : this.searches.searchComposerIds(personIds);

    if (searchStarted) {
      this.close();
    }
  }

  searchSeason(season: string, event?: MouseEvent) {
    event?.stopPropagation();
    if (!season) {
      return;
    }

    if (this.searches.searchSeason(season)) {
      this.close();
    }
  }

  searchAnnId(id: string | number, event?: MouseEvent) {
    event?.stopPropagation();
    if (this.searches.searchAnnIds([id])) {
      this.close();
    }
  }

  searchAmqSongId(id: string | number, event?: MouseEvent) {
    event?.stopPropagation();
    if (this.searches.searchAmqSongIds([id])) {
      this.close();
    }
  }
}
