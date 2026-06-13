import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, OnChanges, SimpleChanges } from '@angular/core';
import { SearchRequestService, RankedStatus } from '../core/services/search-request.service';
import { Subscription } from 'rxjs';

type SongColumnDefinition = {
  key: string;
  header: string;
  defaultVisible: boolean;
  sortable?: boolean;
};

type TableStatsBreakdown = Record<string, number>;

type StatBreakdownEntry = {
  label: string;
  count: number;
  percent: number;
};

type TableStats = {
  songCount: number;
  uniqueAnime: number;
  uniqueArtists: number;
  avgDifficulty: number;
  avgLength: number | null;
  animeTypeBreakdown: StatBreakdownEntry[];
  songTypeBreakdown: StatBreakdownEntry[];
  broadcastBreakdown: StatBreakdownEntry[];
  performanceBreakdown: StatBreakdownEntry[];
};

const EMPTY_TABLE_STATS: TableStats = {
  songCount: 0,
  uniqueAnime: 0,
  uniqueArtists: 0,
  avgDifficulty: 0,
  avgLength: null,
  animeTypeBreakdown: [],
  songTypeBreakdown: [],
  broadcastBreakdown: [],
  performanceBreakdown: [],
};

const SONG_TYPE_SORT_ORDER = ['OP', 'ED', 'IN'];
// Match search-bar advanced filters: Normal → Dubs → Rebroadcasts (plus combined dub+rebroadcast rows).
const BROADCAST_SORT_ORDER = ['Normal', 'Dub', 'Rebroadcast', 'Dub, Rebroadcast'];
// Match search-bar advanced filters Performance row.
const PERFORMANCE_SORT_ORDER = ['Standard', 'Character', 'Chanting', 'Instrumental', 'No Category'];
// Match search-bar advanced filters Media row (shown as Anime types in stats).
const ANIME_TYPE_SORT_ORDER = ['TV', 'Movie', 'OVA', 'ONA', 'Special', 'Doujin'];

type AnimeListSite = {
  img: string;
  alt: string;
  getUrl: (song: any) => string | null;
};

type SongDistLink = {
  label: string;
  title: string;
  field: 'HQ' | 'MQ' | 'audio';
};

@Component({
  selector: 'app-song-table',
  templateUrl: './song-table.component.html',
  styleUrls: ['./song-table.component.css'],
  host: {
    '(document:click)': 'onAnyClick($event)',
    '(document:keydown)': 'onDocumentKeydown($event)',
  },
  standalone: false,
})
export class SongTableComponent implements OnInit, OnDestroy, OnChanges {
  constructor(private searchRequestService: SearchRequestService) {}

  searchErrorMessage: string | null = null;
  private searchErrorSubscription: Subscription | null = null;
  private rankedStatusSubscription: Subscription | null = null;

  @Input() songTable: any;
  @Input() previousBody: any;
  @Input() animeTitleLang: any;

  tableHeaders: string[] = [];
  availableColumns: SongColumnDefinition[] = [];
  columnVisibility: Record<string, boolean> = {};
  showColumnSettings: boolean = false;
  showTableStats = false;
  private readonly columnVisibilityStorageKey = 'songTable.columnVisibility';
  private loadedColumnVisibilityFromStorage = false;

  private readonly allColumns: SongColumnDefinition[] = [
    { key: 'Info', header: 'Info', defaultVisible: true, sortable: false },
    { key: 'ANN ID', header: 'ANN ID', defaultVisible: true },
    { key: 'ANN Song ID', header: 'Song ID', defaultVisible: false },
    { key: 'Lists', header: 'Anime Lists', defaultVisible: false, sortable: false },
    { key: 'Season', header: 'Season', defaultVisible: true },
    { key: 'Anime Category', header: 'Anime Category', defaultVisible: false },
    { key: 'Anime', header: 'Anime', defaultVisible: true },
    { key: 'Broadcast', header: 'Broadcast', defaultVisible: false },
    { key: 'Song Type', header: 'Song Type', defaultVisible: true },
    { key: 'Performance', header: 'Performance', defaultVisible: false },
    { key: 'Song Name', header: 'Song Name', defaultVisible: true },
    { key: 'Artist', header: 'Artist', defaultVisible: true },
    { key: 'Composer', header: 'Composer', defaultVisible: false },
    { key: 'Arranger', header: 'Arranger', defaultVisible: false },
    { key: 'Length', header: 'Length', defaultVisible: false },
    { key: 'Difficulty', header: 'Difficulty', defaultVisible: false },
    { key: 'Song Links', header: 'Song Links', defaultVisible: false, sortable: false },
    { key: 'Play Audio', header: 'Play', defaultVisible: true, sortable: false },
    { key: 'Delete Row', header: 'Del', defaultVisible: true, sortable: false },
  ];

  private readonly naedistBase = 'https://naedist.animemusicquiz.com/';

  readonly animeListSites: AnimeListSite[] = [
    {
      img: 'assets/img/ANN_Logo.png',
      alt: 'Anime News Network',
      getUrl: (song) =>
        `https://www.animenewsnetwork.com/encyclopedia/anime.php?id=${song.annId}`,
    },
    {
      img: 'assets/img/MyAnimeList_Logo.png',
      alt: 'MyAnimeList',
      getUrl: (song) =>
        song.linked_ids?.myanimelist
          ? `https://myanimelist.net/anime/${song.linked_ids.myanimelist}`
          : null,
    },
    {
      img: 'assets/img/AniDB_Logo.png',
      alt: 'Anidb',
      getUrl: (song) =>
        song.linked_ids?.anidb
          ? `https://anidb.net/anime/${song.linked_ids.anidb}`
          : null,
    },
    {
      img: 'assets/img/AniList_logo.png',
      alt: 'Anilist',
      getUrl: (song) =>
        song.linked_ids?.anilist
          ? `https://anilist.co/anime/${song.linked_ids.anilist}`
          : null,
    },
    {
      img: 'assets/img/Kitsu_Logo.png',
      alt: 'Kitsu',
      getUrl: (song) =>
        song.linked_ids?.kitsu
          ? `https://kitsu.app/anime/${song.linked_ids.kitsu}`
          : null,
    },
  ];

  readonly songDistLinks: SongDistLink[] = [
    { label: '720', title: 'Open 720 link', field: 'HQ' },
    { label: '480', title: 'Open 480 link', field: 'MQ' },
    { label: 'MP3', title: 'Open MP3 link', field: 'audio' },
  ];

  private readonly seasonOrder: Record<string, number> = {
    Winter: 0,
    Spring: 1,
    Summer: 2,
    Fall: 3,
    Autumn: 3,
  };

  @Output() mp3PlayerClicked = new EventEmitter();
  playMP3music(song: any) {
    this.currentPlayingSong = song;
    this.mp3PlayerClicked.emit(song);
  }

  @Output() sendSongListtoTable = new EventEmitter();
  sendSongList(currentSongList: any) {
    this.sendSongListtoTable.emit(currentSongList);
  }

  @Output() sendPreviousBody = new EventEmitter();
  sendPrevBody(body: any) {
    this.sendPreviousBody.emit(body);
  }

  ngOnInit() {
    this.initializeColumns();
    this.searchErrorSubscription = this.searchRequestService.searchError$.subscribe(
      (message) => {
        this.searchErrorMessage = message;
      },
    );
    this.rankedStatusSubscription = this.searchRequestService.rankedStatus$.subscribe(
      (status) => {
        this.rankedStatus = status;
      },
    );
  }

  ngOnDestroy() {
    this.searchErrorSubscription?.unsubscribe();
    this.rankedStatusSubscription?.unsubscribe();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.initializeColumns();

    if (changes['songTable']) {
      this.ascendingOrder = false;
      this.refreshTableStats();
      this.sortFunction('ANN ID');
    }
  }

  initializeColumns() {
    this.availableColumns = this.allColumns;

    if (!this.loadedColumnVisibilityFromStorage) {
      this.loadColumnVisibilityFromStorage();
      this.loadedColumnVisibilityFromStorage = true;
    }

    const activeColumnKeys = new Set(this.availableColumns.map((c) => c.key));

    for (const key of Object.keys(this.columnVisibility)) {
      if (!activeColumnKeys.has(key)) {
        delete this.columnVisibility[key];
      }
    }

    for (const column of this.availableColumns) {
      if (this.columnVisibility[column.key] === undefined) {
        this.columnVisibility[column.key] = column.defaultVisible;
      }
    }

    this.tableHeaders = this.availableColumns
      .filter((column) => this.columnVisibility[column.key])
      .map((column) => column.key);

    this.saveColumnVisibilityToStorage();
  }

  getHeaderLabel(columnKey: string) {
    const column = this.availableColumns.find((c) => c.key === columnKey);
    return column ? column.header : columnKey;
  }

  isCenterAlignedColumn(columnKey: string) {
    return columnKey === 'Play Audio' || columnKey === 'Info' || columnKey === 'Delete Row';
  }

  isColumnVisible(columnKey: string) {
    return !!this.columnVisibility[columnKey];
  }

  isColumnSortable(columnKey: string) {
    return (
      this.availableColumns.find((column) => column.key === columnKey)
        ?.sortable !== false
    );
  }

  onHeaderClick(columnKey: string) {
    if (this.isColumnSortable(columnKey)) {
      this.sortFunction(columnKey);
    }
  }

  getDistLink(filename: string | null | undefined) {
    return filename ? `${this.naedistBase}${filename}` : '';
  }

  shouldShowSongLink(song: any, link: SongDistLink) {
    return !!song[link.field];
  }

  toggleColumn(columnKey: string, visible: boolean) {
    this.columnVisibility[columnKey] = visible;
    this.tableHeaders = this.availableColumns
      .filter((column) => this.columnVisibility[column.key])
      .map((column) => column.key);
    this.saveColumnVisibilityToStorage();
  }

  loadColumnVisibilityFromStorage() {
    try {
      const rawValue = localStorage.getItem(this.columnVisibilityStorageKey);
      if (!rawValue) {
        return;
      }

      const parsed = JSON.parse(rawValue);
      if (!parsed || typeof parsed !== 'object') {
        return;
      }

      for (const column of this.allColumns) {
        const value = (parsed as Record<string, unknown>)[column.key];
        if (typeof value === 'boolean') {
          this.columnVisibility[column.key] = value;
        }
      }
    } catch (_error) {
      // Ignore invalid persisted state and keep defaults.
    }
  }

  saveColumnVisibilityToStorage() {
    try {
      localStorage.setItem(
        this.columnVisibilityStorageKey,
        JSON.stringify(this.columnVisibility),
      );
    } catch (_error) {
      // Ignore storage failures.
    }
  }

  toggleColumnSettings(event: Event) {
    event.stopPropagation();
    this.showTableStats = false;
    this.showColumnSettings = !this.showColumnSettings;
  }

  toggleTableStats(event: Event) {
    event.stopPropagation();
    this.showColumnSettings = false;
    this.showTableStats = !this.showTableStats;
  }

  isCurrentPlayingSong(song: any) {
    return song === this.currentPlayingSong;
  }

  maxGridNb: number = 3;

  getGridStyle(itemCount: number) {
    return {
      'grid-template-columns': `repeat(${Math.min(
        this.maxGridNb,
        itemCount,
      )}, 1fr)`,
    };
  }

  getSubGridStyle(itemCount: number) {
    return {
      'grid-template-columns': `repeat(${
        this.maxGridNb - Math.min(this.maxGridNb, itemCount) + 1
      }, 1fr)`,
    };
  }

  lastColName: string = '';
  ascendingOrder: boolean = false;
  showSongInfoPopup: boolean = false;
  songInfoPopupIndex = -1;
  doubleClickPreventer: boolean = false;
  animeJPName: string = '';

  popUpannId: string = '';
  popUpVintage: string = '';
  popUpAnimeType: string = '';
  popUpAnimeCategory: string = '';
  popUpannSongId: string = '';
  popUpSongName: string = '';
  popUpArtist: string = '';
  popUpSongDiff: string = '';
  popUpSongLength: string = '';
  popUpSongCat: string = '';
  popUpannURL: string = '';
  popUpMalID: string = '';
  popUpAnidbID: string = '';
  popUpAnilistID: string = '';
  popUpKitsuID: string = '';
  popUpAnime: string = '';
  popUpHDLink: string = '';
  popUpHDName: string = '';
  popUpMDLink: string = '';
  popUpMDName: string = '';
  popUpAudioLink: string = '';
  popUpAudioName: string = '';
  popUpArtistsInfo: any = [];
  popUpComposersInfo: any = [];
  popUpArrangersInfo: any = [];
  tableStats: TableStats = { ...EMPTY_TABLE_STATS };
  clipboardPopUpStyle: any;
  show: boolean = false;

  rankedStatus: RankedStatus = {
    active: false,
    region: null,
    remainingSeconds: 0,
  };
  currentPlayingSong: any;

  copyToClipboard(event: any, copytext: string) {
    navigator.clipboard.writeText(copytext);
    this.clipboardPopUpStyle = {
      left: event.pageX + 10 + 'px',
      top: event.pageY - 20 + 'px',
    };
    this.show = true;
    setTimeout(() => {
      this.show = false;
    }, 400);
    return;
  }

  computeAverage(array: any[]): number {
    if (!array?.length) {
      return 0;
    }

    const diffs = array
      .filter((song) => song.songDifficulty)
      .map((song) => song.songDifficulty);

    if (!diffs.length) {
      return 0;
    }

    const total = diffs.reduce((sum, item) => sum + item, 0);

    return +(total / diffs.length).toFixed(1);
  }

  refreshTableStats() {
    if (!this.songTable?.length) {
      this.tableStats = { ...EMPTY_TABLE_STATS };
      return;
    }

    const animeIds = new Set<number>();
    const artistIds = new Set<number>();
    const animeTypeCounts: TableStatsBreakdown = {};
    const songTypeCounts: TableStatsBreakdown = {};
    const broadcastCounts: TableStatsBreakdown = {};
    const performanceCounts: TableStatsBreakdown = {};
    const lengths: number[] = [];

    for (const song of this.songTable) {
      if (song.annId != null) {
        animeIds.add(song.annId);
      }

      for (const artistId of this.collectSongArtistIds(song.artists)) {
        artistIds.add(artistId);
      }

      this.incrementStatCount(animeTypeCounts, song.animeType);
      this.incrementStatCount(songTypeCounts, this.normalizeSongType(song.songType));
      this.incrementStatCount(broadcastCounts, this.getBroadcastLabel(song));
      this.incrementStatCount(performanceCounts, song.songCategory);

      if (song.songLength != null && !Number.isNaN(Number(song.songLength))) {
        lengths.push(Number(song.songLength));
      }
    }

    const avgLength = lengths.length
      ? +(lengths.reduce((sum, value) => sum + value, 0) / lengths.length).toFixed(1)
      : null;

    const songCount = this.songTable.length;

    this.tableStats = {
      songCount,
      uniqueAnime: animeIds.size,
      uniqueArtists: artistIds.size,
      avgDifficulty: this.computeAverage(this.songTable),
      avgLength,
      songTypeBreakdown: this.buildStatBreakdownEntries(
        songTypeCounts,
        songCount,
        SONG_TYPE_SORT_ORDER,
      ),
      broadcastBreakdown: this.buildStatBreakdownEntries(
        broadcastCounts,
        songCount,
        BROADCAST_SORT_ORDER,
      ),
      performanceBreakdown: this.buildStatBreakdownEntries(
        performanceCounts,
        songCount,
        PERFORMANCE_SORT_ORDER,
      ),
      animeTypeBreakdown: this.buildStatBreakdownEntries(
        animeTypeCounts,
        songCount,
        ANIME_TYPE_SORT_ORDER,
      ),
    };
  }

  private normalizeSongType(songType: string | null | undefined): string {
    if (!songType?.trim()) {
      return '(none)';
    }

    if (songType.startsWith('Opening')) {
      return 'OP';
    }

    if (songType.startsWith('Ending')) {
      return 'ED';
    }

    if (songType.toLowerCase().includes('insert')) {
      return 'IN';
    }

    return songType.trim();
  }

  private incrementStatCount(counts: TableStatsBreakdown, value: string | null | undefined) {
    const label = value?.trim() || '(none)';
    counts[label] = (counts[label] ?? 0) + 1;
  }

  private collectSongArtistIds(artists: any): number[] {
    if (!artists) {
      return [];
    }

    if (artists.id != null) {
      return [artists.id];
    }

    if (Array.isArray(artists)) {
      return artists.map((artist) => artist?.id).filter((id) => id != null);
    }

    return Object.values(artists)
      .map((artist: any) => artist?.id)
      .filter((id) => id != null);
  }

  private buildStatBreakdownEntries(
    counts: TableStatsBreakdown,
    total: number,
    sortLabels?: string[],
  ): StatBreakdownEntry[] {
    const entries = Object.entries(counts).map(([label, count]) => ({
      label,
      count,
      percent: total ? +((count / total) * 100).toFixed(1) : 0,
    }));

    if (sortLabels?.length) {
      return entries.sort((left, right) => {
        const leftIndex = sortLabels.indexOf(left.label);
        const rightIndex = sortLabels.indexOf(right.label);
        const leftRank = leftIndex === -1 ? sortLabels.length + 1 : leftIndex;
        const rightRank = rightIndex === -1 ? sortLabels.length + 1 : rightIndex;

        if (leftRank !== rightRank) {
          return leftRank - rightRank;
        }

        return left.label.localeCompare(right.label);
      });
    }

    return entries.sort((left, right) => left.label.localeCompare(right.label));
  }

  formatAvgLength(seconds: number | null) {
    if (seconds == null) {
      return '—';
    }

    return `${seconds}s`;
  }

  sortArtists(
    artists: { names: string[]; groups: string[]; members: string[] }[],
  ) {
    // Create a new, sorted array of artists
    const sortedArtists = artists
      .map((artist) => artist)
      .sort((a, b) => {
        // Use the optional chaining operator to safely access the group and member lengths
        // If either property is missing, the length will be treated as -1 (to compensate with title header)
        // for names specifically, 0 and 1 will be treated as -1 as well
        let aLength =
          ((a.names?.length ?? -1) <= 1 ? -1 : (a.names?.length ?? -1)) +
          (a.groups?.length ?? -1) +
          (a.members?.length ?? -1);
        let bLength =
          ((b.names?.length ?? -1) <= 1 ? -1 : (b.names?.length ?? -1)) +
          (b.groups?.length ?? -1) +
          (b.members?.length ?? -1);

        // Sort the artists based on their group and member lengths
        return aLength - bLength;
      });

    // Return the sorted array
    return sortedArtists;
  }

  getTypeAndNumber(songType: string) {
    const words = songType.split(' ');
    const type = words[0];
    const number = parseInt(words[1]) ? parseInt(words[1]) : 0;

    return { type, number };
  }

  compareSongsType(songType1: string, songType2: string) {
    const type1 = this.getTypeAndNumber(songType1);
    const type2 = this.getTypeAndNumber(songType2);

    const songTypes = ['Opening', 'Ending', 'Insert'];

    return (
      songTypes.indexOf(type1.type) - songTypes.indexOf(type2.type) ||
      type1.number - type2.number
    );
  }

  parseVintage(vintage: string) {
    const parsed = /^([A-Za-z]+)\s+(\d{4})$/.exec((vintage || '').trim());

    if (!parsed) {
      return { season: '', year: null, seasonIndex: 4 };
    }

    const normalizedSeason =
      parsed[1].charAt(0).toUpperCase() + parsed[1].slice(1).toLowerCase();
    const year = parseInt(parsed[2], 10);
    const seasonIndex = this.seasonOrder[normalizedSeason] ?? 4;

    return { season: normalizedSeason, year, seasonIndex };
  }

  getSeasonYearValue(song: any) {
    const parsed = this.parseVintage(song?.animeVintage || '');
    if (parsed.year === null) {
      return song?.animeVintage || '-';
    }

    return `${parsed.season} ${parsed.year}`;
  }

  getBroadcastLabel(song: any): string {
    const labels: string[] = [];
    if (song.isDub) {
      labels.push('Dub');
    }
    if (song.isRebroadcast) {
      labels.push('Rebroadcast');
    }
    return labels.length ? labels.join(', ') : 'Normal';
  }

  getSortValue(song: any, colName: string) {
    switch (colName) {
      case 'ANN ID':
        return Number(song.annId ?? -1);
      case 'ANN Song ID':
        return song.annSongId === -1 ? -1 : Number(song.annSongId ?? -1);
      case 'Song Type':
        return song.songType;
      case 'Song Name':
        return song.songName;
      case 'Artist':
        return song.songArtist;
      case 'Anime':
        return this.animeTitleLang == 'JP'
          ? song.animeJPName
          : song.animeENName;
      case 'Season': {
        const parsed = this.parseVintage(song.animeVintage || '');
        if (parsed.year === null) {
          return -1;
        }

        return parsed.year * 10 + parsed.seasonIndex;
      }
      case 'Anime Category':
        return song.animeCategory;
      case 'Broadcast': {
        if (song.isDub && song.isRebroadcast) {
          return 3;
        }
        if (song.isRebroadcast) {
          return 2;
        }
        if (song.isDub) {
          return 1;
        }
        return 0;
      }
      case 'Performance':
        return song.songCategory;
      case 'Difficulty':
        return Number(song.songDifficulty ?? -1);
      case 'Length':
        return Number(song.songLength ?? -1);
      case 'Composer':
        return song.songComposer;
      case 'Arranger':
        return song.songArranger;
      default:
        return song[colName];
    }
  }

  comparePrimitiveValues(aValue: any, bValue: any) {
    if (aValue === bValue) return 0;
    if (aValue === undefined || aValue === null) return 1;
    if (bValue === undefined || bValue === null) return -1;

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return aValue < bValue ? -1 : 1;
    }

    return String(aValue).localeCompare(String(bValue), undefined, {
      numeric: true,
      sensitivity: 'base',
    });
  }

  compareTwoSongs(colName: string, a: any, b: any) {
    let comparison;

    if (colName === 'Song Type') {
      comparison = this.compareSongsType(a['songType'], b['songType']);
    } else {
      comparison = this.comparePrimitiveValues(
        this.getSortValue(a, colName),
        this.getSortValue(b, colName),
      );
    }

    if (comparison === 0 && colName === 'ANN ID') {
      comparison = this.compareSongsType(a['songType'], b['songType']);
    } else if (comparison === 0) {
      comparison = this.comparePrimitiveValues(a['annId'], b['annId']);
    }

    return this.ascendingOrder ? comparison : -comparison;
  }

  sortFunction(colName: string) {
    if (!this.songTable || !this.isColumnSortable(colName)) {
      return;
    }

    if (this.lastColName !== colName) {
      this.lastColName = colName;
      this.ascendingOrder = true;
    } else {
      this.ascendingOrder = !this.ascendingOrder;
    }

    this.songTable.sort((a: any, b: any) =>
      this.compareTwoSongs(colName, a, b),
    );
  }

  onAnyClick(event: MouseEvent) {
    const target = event.target as Node;

    if (this.showTableStats) {
      const statsPopover = document.querySelector('.table-stats-popover');
      if (!statsPopover?.contains(target)) {
        this.showTableStats = false;
      }
    }

    if (this.showColumnSettings) {
      const columnSettingsArea = document.querySelector('.table-controls-actions');
      if (!columnSettingsArea?.contains(target)) {
        this.showColumnSettings = false;
      }
    }

    if (this.showSongInfoPopup && !this.doubleClickPreventer) {
      this.showSongInfoPopup = false;
      this.songInfoPopupIndex = -1;
    } else if (this.showSongInfoPopup) {
      this.doubleClickPreventer = !this.doubleClickPreventer;
    }
  }

  onDocumentKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      if (this.showSongInfoPopup) {
        this.showSongInfoPopup = false;
        this.songInfoPopupIndex = -1;
        return;
      }

      if (this.showTableStats) {
        this.showTableStats = false;
        return;
      }

      if (this.showColumnSettings) {
        this.showColumnSettings = false;
        return;
      }

      return;
    }

    if (!this.showSongInfoPopup) {
      return;
    }

    const tag = (event.target as HTMLElement).tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
      return;
    }

    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      this.navigateSongInfoPopup(-1);
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      this.navigateSongInfoPopup(1);
    }
  }

  navigateSongInfoPopup(delta: number) {
    const length = this.songTable?.length ?? 0;
    if (length <= 1) {
      return;
    }

    const nextIndex =
      (this.songInfoPopupIndex + delta + length) % length;
    this.songInfoPopupIndex = nextIndex;
    this.populateSongInfoPopup(this.songTable[nextIndex]);
    this.scrollSongInfoModalToTop();
  }

  private scrollSongInfoModalToTop() {
    setTimeout(() => {
      document.getElementById('myModal')?.scrollTo(0, 0);
    });
  }

  getColumnDisplayValue(song: any, colName: string) {
    switch (colName) {
      case 'ANN ID':
        return song.annId ?? '-';
      case 'ANN Song ID':
        return song.annSongId != null && song.annSongId !== -1 ? song.annSongId : '-';
      case 'Song Type':
        return song.songType || '-';
      case 'Song Name':
        return song.songName || '-';
      case 'Artist':
        return song.songArtist || '-';
      case 'Anime':
        return this.animeTitleLang == 'JP'
          ? song.animeJPName
          : song.animeENName;
      case 'Season':
        return this.getSeasonYearValue(song);
      case 'Anime Category':
        return song.animeCategory || '-';
      case 'Broadcast':
        return this.getBroadcastLabel(song);
      case 'Performance':
        return song.songCategory || '-';
      case 'Difficulty':
        return song.songDifficulty != null ? `${song.songDifficulty}%` : '-';
      case 'Length':
        return song.songLength != null ? `${song.songLength}s` : '-';
      case 'Composer':
        return song.songComposer || '-';
      case 'Arranger':
        return song.songArranger || '-';
      default:
        return song[colName] ?? '-';
    }
  }

  getColumnCopyValue(song: any, colName: string) {
    switch (colName) {
      case 'ANN ID':
        return song.annId != null ? String(song.annId) : '';
      case 'ANN Song ID':
        return song.annSongId != null && song.annSongId !== -1
          ? String(song.annSongId)
          : '';
      case 'Song Type':
        return song.songType || '';
      case 'Song Name':
        return song.songName || '';
      case 'Artist':
        return song.songArtist || '';
      case 'Anime':
        return this.animeTitleLang == 'JP'
          ? song.animeJPName
          : song.animeENName;
      case 'Season':
        return this.getSeasonYearValue(song);
      case 'Anime Category':
        return song.animeCategory || '';
      case 'Broadcast':
        return this.getBroadcastLabel(song);
      case 'Performance':
        return song.songCategory || '';
      case 'Difficulty':
        return song.songDifficulty != null ? String(song.songDifficulty) : '';
      case 'Length':
        return song.songLength != null ? String(song.songLength) : '';
      case 'Composer':
        return song.songComposer || '';
      case 'Arranger':
        return song.songArranger || '';
      default:
        return song[colName] != null ? String(song[colName]) : '';
    }
  }

  displaySongInfoPopup(song: any) {
    const index = this.songTable?.findIndex((row: any) => row === song) ?? -1;

    if (this.showSongInfoPopup && index >= 0 && index === this.songInfoPopupIndex) {
      this.showSongInfoPopup = false;
      this.songInfoPopupIndex = -1;
      return;
    }

    this.songInfoPopupIndex = index >= 0 ? index : 0;
    this.populateSongInfoPopup(song);
    this.showSongInfoPopup = true;
    this.doubleClickPreventer = true;
  }

  private populateSongInfoPopup(song: any) {
    this.popUpannURL =
      'https://www.animenewsnetwork.com/encyclopedia/anime.php?id=' +
      song.annId;
    this.popUpannId = song.annId;
    this.popUpVintage = song.animeVintage;
    this.popUpAnimeType = song.animeType;
    this.popUpAnimeCategory = song.animeCategory;
    this.popUpannSongId = song.annSongId != -1 ? song.annSongId : null;
    this.popUpAnime =
      this.animeTitleLang == 'JP' ? song.animeJPName : song.animeENName;
    this.popUpMalID = song.linked_ids.myanimelist;
    this.popUpAnidbID = song.linked_ids.anidb;
    this.popUpAnilistID = song.linked_ids.anilist;
    this.popUpKitsuID = song.linked_ids.kitsu;
    this.popUpSongName = song.songName;
    this.popUpArtist = song.songArtist;
    this.popUpSongDiff = song.songDifficulty;
    this.popUpSongLength = song.songLength;
    this.popUpSongCat = song.songCategory;
    this.popUpHDName = song.HQ;
    this.popUpHDLink = song.HQ
      ? 'https://naedist.animemusicquiz.com/' + song.HQ
      : '';
    this.popUpMDName = song.MQ;
    this.popUpMDLink = song.MQ
      ? 'https://naedist.animemusicquiz.com/' + song.MQ
      : '';
    this.popUpAudioName = song.audio;
    this.popUpAudioLink = song.audio
      ? 'https://naedist.animemusicquiz.com/' + song.audio
      : '';
    this.popUpArtistsInfo = this.sortArtists(song.artists);
    this.popUpComposersInfo = song.composers;
    this.popUpArrangersInfo = song.arrangers;
    this.animeJPName = song.animeJPName;
  }

  deleteRowEntry(song: any) {
    const id = this.songTable.findIndex((obj: any) => obj === song);
    this.songTable.splice(id, 1);
    this.refreshTableStats();
  }

  searchArtistIds(artists: any) {
    let id_arr;
    if (artists.id) {
      id_arr = [artists.id];
    } else {
      id_arr = [];
      for (let artist in artists) {
        id_arr.push(artists[artist].id);
      }
    }

    let body = {
      artist_ids: id_arr,
      group_granularity: 0,
      max_other_artist: 99,
    };

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return;
    }

    this.previousBody = body;
    this.sendPrevBody(body);

    let currentSongList;
    currentSongList = this.searchRequestService
      .artistIdsSearchRequest(body)
      .subscribe((data) => {
        currentSongList = data;
        this.sendSongList(currentSongList);
      });
  }

  searchComposerIds(composers: any) {
    let id_arr;
    if (composers.id) {
      id_arr = [composers.id];
    } else {
      id_arr = [];
      for (let composer in composers) {
        id_arr.push(composers[composer].id);
      }
    }

    let body = {
      composer_ids: id_arr,
      arrangement: true,
    };

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return;
    }

    this.previousBody = body;
    this.sendPrevBody(body);

    let currentSongList;
    currentSongList = this.searchRequestService
      .composerIdsSearchRequest(body)
      .subscribe((data) => {
        currentSongList = data;
        this.sendSongList(currentSongList);
      });
  }

  searchAnnId(id: any) {
    let body = {
      ann_ids: [id],
    };

    if (JSON.stringify(body) === JSON.stringify(this.previousBody)) {
      return;
    }

    this.previousBody = body;
    this.sendPrevBody(body);

    let currentSongList;
    currentSongList = this.searchRequestService
      .annIdsSearchRequest(body)
      .subscribe((data) => {
        currentSongList = data;
        this.sendSongList(currentSongList);
      });
  }
}
