import { computed, DestroyRef, inject, Injectable, signal, Signal, WritableSignal } from '@angular/core';
import { ApiClient, errorMessage } from '../../core/api-client.service';
import { DatabaseStats } from './stats-types';
import {
  LabelView,
  artistTable,
  creditTable,
  rankingTable,
  labelTable,
  friendlyLabel,
  formatNumber,
  formatShare,
  makeTable,
} from './stats-tables';
import { animePanel, difficultyPanel, lengthPanel, seasonPanel } from './stats-panels';

const DEFAULTS = {
  artistView: 'overview',
  creditView: 'coverage',
  creditRankingRole: 'performer',
  genreView: 'counts',
  genreSort: 'count',
  genreFilter: '',
  tagView: 'counts',
  tagSort: 'count',
  tagFilter: '',
  seasonView: 'graph',
  seasonPeriod: 'seasons',
  seasonMetric: 'songs',
  seasonBreakdown: 'none',
  songsAnimeView: 'graph',
  songsAnimeFormat: 'All',
  songsAnimeMetric: 'distribution',
  difficultyView: 'graph',
  difficultyGroup: 'all',
  difficultyBucket: '1',
  difficultyValues: 'count',
  lengthView: 'graph',
  lengthGroup: 'all',
  lengthBucket: '15',
  lengthValues: 'count',
};

export type StatsControl = keyof typeof DEFAULTS;

@Injectable()
export class StatsState {
  private readonly api = inject(ApiClient);
  readonly data = signal<DatabaseStats | null>(null);
  readonly loading = signal(true);
  readonly error = signal('');
  readonly controls = Object.fromEntries(Object.entries(DEFAULTS).map(([key, value]) => [key, signal(value)])) as Record<StatsControl, WritableSignal<string>>;
  readonly animeFormats = computed(() => Object.keys(this.data()?.song_analysis.songs_per_anime || {}));
  readonly genres = this.fromData(data => labelTable(
    data, 'genre', this.controls.genreView() as LabelView,
    this.controls.genreFilter().trim().toLowerCase(), this.controls.genreSort()));
  readonly tags = this.fromData(data => labelTable(
    data, 'tag', this.controls.tagView() as LabelView,
    this.controls.tagFilter().trim().toLowerCase(), this.controls.tagSort()));
  readonly artists = this.fromData(data => artistTable(data, this.controls.artistView()));
  readonly credits = this.fromData(data => creditTable(data, this.controls.creditView()));
  readonly ranking = this.fromData(data => rankingTable(data, this.controls.creditRankingRole()));
  readonly season = this.fromData(data => seasonPanel(
    data, this.controls.seasonPeriod(), this.controls.seasonMetric(), this.controls.seasonBreakdown()
  ));
  readonly anime = this.fromData(data => animePanel(
    data, this.controls.songsAnimeFormat(), this.controls.songsAnimeMetric(), this.controls.songsAnimeView()
  ));
  readonly difficulty = this.fromData(data => difficultyPanel(data, {
    group: this.controls.difficultyGroup(),
    bucketSize: Number(this.controls.difficultyBucket()),
    values: this.controls.difficultyValues(),
    view: this.controls.difficultyView(),
  }));
  readonly length = this.fromData(data => lengthPanel(data, {
    group: this.controls.lengthGroup(),
    bucketSize: Number(this.controls.lengthBucket()),
    values: this.controls.lengthValues(),
    view: this.controls.lengthView(),
  }));
  readonly links = this.fromData(data => makeTable(
    ['Formats', 'Songs', 'Share'],
    Object.entries(data.links_by_combination).map(([label, count]) => [
      label, formatNumber(count), formatShare(count, data.total_songs),
    ]),
    [1, 2]));
  readonly originals = computed(() => {
    const data = this.data();
    if (!data) {
      return null;
    }
    const labels: Record<string, string> = {
      artist_aliases: 'Artists with original aliases',
      anime_titles: 'Anime titles',
      anime_alt_titles: 'Anime with original alt titles',
      song_titles: 'Song titles',
      performer_names: 'Performer credits',
      composer_names: 'Composer credits',
      arranger_names: 'Arranger credits',
    };
    const formatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
    return makeTable(['Field', 'Populated', 'Records', 'Coverage'], Object.entries(data.original_name_coverage).map(([key, value]) => [
      labels[key] || friendlyLabel(key),
      formatNumber(value.present),
      formatNumber(value.total),
      formatShare(value.present, value.total, formatter),
    ]), [1, 2, 3]);
  });
  readonly missing = computed(() => {
    const data = this.data();
    if (!data) {
      return [];
    }
    const hidden = ['songs_without_season', 'songs_without_genre', 'songs_without_tag'];
    return Object.entries(data.missing_data).filter(([key]) => !hidden.includes(key)).map(([key, value]) => {
      const total = key.startsWith('anime_') ? data.total_anime : data.total_songs;
      const completeness = total ? Math.max(0, (total - value) / total * 100) : 0;
      return {
        label: friendlyLabel(key),
        value: formatNumber(value),
        completeness,
        text: new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(completeness) + '% complete'
      };
    });
  });
  readonly idCoverage = computed(() => {
    const data = this.data();
    if (!data) {
      return [];
    }
    const groups: [string, number, [string, string][]][] = [
      [
        'Anime',
        data.total_anime,
        [
          ['ANN ID', 'ann'],
          ['MyAnimeList', 'myanimelist'],
          ['AniList', 'anilist'],
          ['Kitsu', 'kitsu'],
          ['AniDB', 'anidb']
        ]
      ],
      ['Songs', data.total_songs, [['ANN song ID', 'ann_song'], ['AMQ song ID', 'amq_song']]],
    ];
    return groups.map(([name, total, entries]) => ({
      title: name + ' \u00B7 ' + formatNumber(total),
      rows: entries.map(([label, key]) => {
        const count = data.external_id_coverage[key];
        return {
          label,
          value: formatNumber(count.present) + ' \u00B7 ' + formatShare(count.present, count.total),
          width: count.total ? count.present / count.total * 100 : 0
        };
      }),
    }));
  });
  private request: AbortController | null = null;

  constructor() {
    inject(DestroyRef).onDestroy(() => this.request?.abort());
    void this.load();
  }

  private fromData<T>(model: (data: DatabaseStats) => T): Signal<T | null> {
    return computed(() => {
      const data = this.data();
      return data ? model(data) : null;
    });
  }

  setControl(key: StatsControl, value: string): void {
    this.controls[key].set(value);
    if (key === 'genreView') {
      this.controls.genreSort.set(this.genres()?.sortKey || 'count');
    }
    if (key === 'tagView') {
      this.controls.tagSort.set(this.tags()?.sortKey || 'count');
    }
  }

  async load(): Promise<void> {
    this.request?.abort();
    const request = this.request = new AbortController();
    this.loading.set(true);
    this.error.set('');
    try {
      const data = await this.api.requestOnce<DatabaseStats>('/api/database_stats', { signal: request.signal });
      if (request.signal.aborted) {
        return;
      }
      if (!data.song_analysis || !data.artist_credits || !Number.isFinite(data.total_songs)) {
        throw new Error('Invalid statistics response.');
      }
      this.data.set(data);
      if (!data.song_analysis.songs_per_anime[this.controls.songsAnimeFormat()]) {
        this.controls.songsAnimeFormat.set('All');
      }
    } catch (error) {
      if (!request.signal.aborted) {
        this.error.set('Statistics could not be loaded. ' + errorMessage(error));
      }
    } finally {
      if (!request.signal.aborted) {
        this.loading.set(false);
      }
    }
  }
}
