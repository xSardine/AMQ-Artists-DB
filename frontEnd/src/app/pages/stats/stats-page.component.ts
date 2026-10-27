import { ChangeDetectionStrategy, Component, computed, inject, signal, Signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ToolbarComponent } from '../../shared/layout/toolbar.component';
import { StatsSettingsDialogComponent } from './stats-settings-dialog.component';
import { formatLocalTimestamp } from '../../shared/utils/date-format';
import { StatsState, StatsControl } from './stats-state';
import { StatsChartComponent } from './stats-chart.component';
import { StatsCompositionComponent } from './stats-composition.component';
import { StatsTableComponent } from './stats-table.component';
import { formatNumber } from './stats-tables';
import { StatsPanel } from './stats-panels';

interface Control {
  key: StatsControl;
  label: string;
  options: [string, string][];
  hiddenWhen?: string;
}

interface Panel {
  id: string;
  title: string;
  model: Signal<StatsPanel | null>;
  view: StatsControl;
  wide?: boolean;
  half?: boolean;
  views: [string, string][];
  controls: Control[];
  note?: string;
}
const LABEL_VIEWS: [string, string][] = [
  ['counts', 'Counts'],
  ['difficulty', 'Difficulty'],
  ['length', 'Length'],
  ['types', 'Song types'],
  ['coverage', 'Coverage']
];
const GROUPS: [string, string][] = [
  ['all', 'All'],
  ['song_type', 'Song type'],
  ['performance', 'Performance'],
  ['anime_format', 'Anime format'],
  ['decade', 'Decade']
];

@Component({
  selector: 'app-stats-page',
  imports: [
    FormsModule,
    ToolbarComponent,
    StatsSettingsDialogComponent,
    StatsChartComponent,
    StatsCompositionComponent,
    StatsTableComponent,
  ],
  providers: [StatsState],
  templateUrl: './stats-page.component.html',
  styleUrl: './stats-page.component.css',
  host: { style: 'display: block' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatsPageComponent {
  readonly state = inject(StatsState);
  readonly settingsOpen = signal(false);
  readonly formatTimestamp = formatLocalTimestamp;
  readonly formatNumber = formatNumber;
  readonly labelViews = LABEL_VIEWS;
  readonly totals = computed(() => {
    const data = this.state.data();
    return [
      ['Songs', data?.total_songs],
      ['Anime', data?.total_anime],
      ['Artists', data?.total_artists],
      ['Seasons', data?.total_seasons]
    ]
      .map(([label, value]) => ({
        label,
        value: typeof value === 'number' ? formatNumber(value) : '\u2014'
      }));
  });
  readonly compositionPanels = [
    {
      title: 'Song Types',
      field: 'songs_by_type' as const
    },
    {
      title: 'Broadcast',
      field: 'songs_by_broadcast' as const
    },
    {
      title: 'Performance',
      field: 'songs_by_performance' as const
    },
    {
      title: 'Anime Format',
      field: 'songs_by_anime_type' as const
    },
  ];
  readonly labels = [
    {
      id: 'genre',
      title: 'Genres',
      model: this.state.genres,
      filter: 'genreFilter' as const,
      view: 'genreView' as const,
      sort: 'genreSort' as const
    },
    {
      id: 'tag',
      title: 'Tags',
      model: this.state.tags,
      filter: 'tagFilter' as const,
      view: 'tagView' as const,
      sort: 'tagSort' as const
    },
  ];
  readonly artistViews: [string, string][] = [
    ['overview', 'Overview'],
    ['roles', 'Roles'],
    ['aliases', 'Aliases'],
    ['groups', 'Group rosters'],
    ['lineups', 'Lineup counts'],
    ['reach', 'Song reach']
  ];
  readonly creditViews: [string, string][] = [
    ['coverage', 'ID coverage'],
    ['missing', 'Missing ID context'],
    ['people', 'People'],
    ['groups', 'Group credits'],
    ['sizes', 'IDs per song']
  ];
  readonly rankingRoles: [string, string][] = [
    ['performer', 'Performers'],
    ['composer', 'Composers'],
    ['arranger', 'Arrangers'],
    ['all', 'All roles']
  ];
  readonly panels = computed<Panel[]>(() => [
    {
      id: 'season',
      title: 'Songs by Season',
      model: this.state.season,
      view: 'seasonView',
      wide: true,
      views: [['graph', 'Graph'], ['table', 'Table']],
      controls: [
        {
          key: 'seasonPeriod',
          label: 'Period',
          options: [['seasons', 'Season'], ['years', 'Year']]
        },
        {
          key: 'seasonMetric',
          label: 'Metric',
          options: [
            ['songs', 'Songs'],
            ['anime', 'Anime'],
            ['density', 'Songs per anime'],
            ['difficulty', 'Median guess rate'],
            ['length', 'Median length']
          ]
        },
        {
          key: 'seasonBreakdown',
          label: 'Breakdown',
          options: [['none', 'None'], ['song_type', 'Song type'], ['anime_format', 'Anime format']]
        },
      ],
      note: 'Dates are anime vintage. Measurements exclude missing values; counts include repeated song appearances.',
    },
    {
      id: 'songs-anime',
      title: 'Songs per Anime',
      model: this.state.anime,
      view: 'songsAnimeView',
      views: [['graph', 'Graph'], ['table', 'Table'], ['most', 'Most songs']],
      controls: [
        {
          key: 'songsAnimeMetric',
          label: 'Metric',
          options: [['distribution', 'Distribution'], ['cumulative', 'Cumulative']],
          hiddenWhen: 'most'
        },
        {
          key: 'songsAnimeFormat',
          label: 'Format',
          options: this.state.animeFormats().map(format => [format, format])
        },
      ],
    },
    {
      id: 'difficulty',
      title: 'Song Difficulty',
      model: this.state.difficulty,
      view: 'difficultyView',
      half: true,
      views: [['graph', 'Graph'], ['table', 'Table'], ['summary', 'Summary']],
      controls: [
        {
          key: 'difficultyGroup',
          label: 'Group',
          options: GROUPS
        },
        {
          key: 'difficultyBucket',
          label: 'Buckets',
          hiddenWhen: 'summary',
          options: [['1', '1 point'], ['5', '5 points'], ['10', '10 points']]
        },
        {
          key: 'difficultyValues',
          label: 'Values',
          hiddenWhen: 'summary',
          options: [['count', 'Songs'], ['share', '% of known songs']]
        },
      ],
    },
    {
      id: 'length',
      title: 'Song Length',
      model: this.state.length,
      view: 'lengthView',
      half: true,
      views: [['graph', 'Graph'], ['table', 'Table'], ['summary', 'Summary']],
      controls: [
        {
          key: 'lengthGroup',
          label: 'Group',
          options: GROUPS
        },
        {
          key: 'lengthBucket',
          label: 'Buckets',
          hiddenWhen: 'summary',
          options: [['5', '5 seconds'], ['15', '15 seconds'], ['30', '30 seconds']]
        },
        {
          key: 'lengthValues',
          label: 'Values',
          hiddenWhen: 'summary',
          options: [['count', 'Songs'], ['share', '% of known songs']]
        },
      ],
    },
  ]);
}
