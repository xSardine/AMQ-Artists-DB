import type { ChartConfiguration } from 'chart.js';
import type { DatabaseStats, MeasurementSummary, SongDistribution, SongSummary } from './stats-types';
import type { StatsTable } from './stats-table.component';
import { formatDuration, formatMeasurement, formatNumber, formatShare, makeTable } from './stats-tables';

const percent = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });
const compare = new Intl.Collator('en', {
  sensitivity: 'base',
  numeric: true
}).compare;

export interface StatsPanel {
  title: string;
  chart: StatsChartConfiguration;
  chartDescription: string;
  table: StatsTable;
  note: string;
  coverage: string;
  summary: string;
}

export interface StatsChartPoint {
  x: string | number;
  y: number | null;
}

export type StatsChartConfiguration = ChartConfiguration<'bar' | 'line', StatsChartPoint[], string>;

type ChartRow = [string, number | null];

interface ChartSeries {
  label: string;
  values: (number | null)[];
}

interface PanelChartOptions {
  series?: ChartSeries[];
  numericAxis?: boolean;
  type?: 'bar' | 'line';
  stacked?: boolean;
  integerValues?: boolean;
  formatValue?: (value: number) => string;
  labelPrefix?: string;
  unit?: string;
  description?: string;
}

function panel(
  title: string,
  rows: ChartRow[],
  table: StatsTable,
  options: PanelChartOptions,
  extra: Partial<StatsPanel> = {},
): StatsPanel {
  const labels = rows.map(([label]) => label);
  const series = options.series ?? [{ label: '', values: rows.map(([, value]) => value) }];
  const formatValue = options.formatValue ?? formatNumber;
  const unit = options.unit ?? 'songs';

  return {
    title,
    chartDescription: options.description ?? title,
    chart: {
      type: options.type ?? 'line',
      data: {
        labels,
        datasets: series.map(group => ({
          label: group.label,
          data: labels.map((label, index) => ({
            x: options.numericAxis ? Number(label) : label,
            y: group.values[index] ?? null,
          })),
          borderWidth: 2,
          pointRadius: 1.5,
          pointHoverRadius: 4,
          spanGaps: false,
        })),
      },
      options: {
        interaction: { mode: 'index', axis: 'x', intersect: false },
        scales: {
          x: {
            ...(options.numericAxis ? {
              type: 'linear' as const,
              bounds: 'data' as const,
              ticks: {
                maxTicksLimit: 6,
                maxRotation: 0,
                precision: 0,
                callback: (value: string | number) => String(value),
              },
            } : {
              type: 'category' as const,
              ticks: { maxTicksLimit: 6, maxRotation: 0 },
            }),
            stacked: options.stacked ?? false,
            grid: { display: false },
          },
          y: {
            type: 'linear',
            beginAtZero: true,
            stacked: options.stacked ?? false,
            ticks: {
              precision: (options.integerValues ?? !options.formatValue) ? 0 : undefined,
              callback: value => formatValue(Number(value)),
            },
          },
        },
        plugins: {
          legend: {
            display: series.length > 1,
            position: 'bottom',
            labels: { boxWidth: 10, boxHeight: 10, padding: 10 },
          },
          tooltip: {
            callbacks: {
              title: items => (options.labelPrefix ?? '') + (labels[items[0]?.dataIndex] ?? ''),
              label: item => {
                const label = item.dataset.label ? item.dataset.label + ': ' : '';
                if (item.parsed.y === null) {
                  return label + '\u2014';
                }
                return label + formatValue(item.parsed.y) + (unit ? ' ' + unit : '');
              },
            },
          },
        },
      },
    },
    table,
    note: '',
    coverage: '',
    summary: '',
    ...extra,
  };
}

export function seasonPanel(
  stats: DatabaseStats,
  period: string,
  metric: string,
  breakdown: string,
): StatsPanel {
  const isYear = period === 'years';
  const periods = Object.entries(stats.song_analysis[isYear ? 'years' : 'seasons']);
  const names: Record<string, string> = {
    songs: 'Songs',
    anime: 'Anime',
    density: 'Songs per Anime',
    difficulty: 'Median Guess Rate',
    length: 'Median Length'
  };
  const title = names[metric] + ' by ' + (isYear ? 'Year' : 'Season');
  const amount = (data: SongSummary | undefined): number | null => {
    if (!data) {
      return ['difficulty', 'length', 'density'].includes(metric) ? null : 0;
    }
    if (metric === 'density') {
      return data.anime ? data.songs / data.anime : null;
    }
    if (metric === 'difficulty' || metric === 'length') {
      return data[metric].median;
    }
    return data[metric as 'songs' | 'anime'];
  };
  const format = (value: number | null): string => value === null ? '\u2014' : metric === 'length' ? formatDuration(value)
    : metric === 'difficulty' ? percent.format(value) + '%' : metric === 'density' ? percent.format(value) : formatNumber(value);
  const dimension = breakdown as 'song_type' | 'anime_format';
  const groups = breakdown === 'none' ? [names[metric]]
    : [...new Set(periods.flatMap(([, data]) => Object.keys(data[dimension])))].sort(compare);
  const series = groups.map(label => ({
    label,
    values: periods.map(([, data]) => amount(breakdown === 'none' ? data.overall : data[dimension][label])),
  }));
  const rows: ChartRow[] = periods.map(([label], index) => [label, series[0]?.values[index] ?? null]);
  return panel(title, rows, makeTable([isYear ? 'Year' : 'Season', ...groups],
    periods.map(([label], index) => [label, ...series.map(group => format(group.values[index]))]),
    groups.map((_, index) => index + 1)), {
    numericAxis: isYear && periods.every(([label]) => Number.isFinite(Number(label))),
    integerValues: metric === 'songs' || metric === 'anime',
    series,
    formatValue: format,
    unit: '',
    description: title + ', grouped by ' + breakdown.replaceAll('_', ' '),
  });
}

export function animePanel(
  stats: DatabaseStats,
  format: string,
  metric: string,
  view: string,
): StatsPanel {
  const data = stats.song_analysis.songs_per_anime[format] || stats.song_analysis.songs_per_anime.All;
  const cumulativeView = metric === 'cumulative';
  const summary = data.anime
    ? formatNumber(data.anime) + ' anime \u00B7 Median: ' + percent.format(data.median!) + ' songs \u00B7 90th percentile: '
    + percent.format(data.p90!) + ' \u00B7 Maximum: ' + formatNumber(data.maximum!)
    : 'No anime in this group.';
  if (view === 'most') {
    return panel('Songs per Anime', [], makeTable(['Anime', 'OP', 'ED', 'Insert', 'Total'],
      data.most_songs.map(anime => [
        anime.name,
        ...['Opening', 'Ending', 'Insert'].map(type => formatNumber(anime.song_types[type])),
        formatNumber(anime.songs)
      ]),
      [1, 2, 3, 4]), {}, { summary });
  }
  let cumulative = 0;
  const rows: ChartRow[] = Object.entries(data.distribution).map(([count, anime]) => {
    cumulative += anime;
    return [count, cumulativeView ? cumulative / data.anime * 100 : anime];
  });
  const countFormat = (value: number) => cumulativeView ? percent.format(value) + '%' : formatNumber(value);
  return panel('Songs per Anime', rows, makeTable(
    [
      cumulativeView ? 'At most this many songs' : 'Songs per anime',
      cumulativeView ? 'Anime share' : 'Anime'
    ],
    rows.map(([label, value]) => [label, countFormat(value ?? 0)]), [1]), {
    numericAxis: true,
    unit: cumulativeView ? '' : 'anime',
    labelPrefix: cumulativeView ? 'At most ' : 'Songs per anime: ',
    formatValue: cumulativeView ? countFormat : undefined,
    description: cumulativeView ? 'Cumulative percentage of anime by song count' : 'Anime counts by number of songs',
  }, { summary });
}

interface DistributionControls {
  group: string;
  bucketSize: number;
  values: string;
  view: string;
}

interface DistributionDefinition {
  title: string;
  heading: string;
  note: string;
  description: string;
  bucketUnit: string;
  maximum?: number;
  measurement: (summary: SongSummary) => MeasurementSummary;
  counts: (data: SongDistribution) => Record<string, number>;
  formatBucket: (value: number) => string;
  formatMeasurement: (value: number | null | undefined) => string;
}

const DIFFICULTY_DISTRIBUTION: DistributionDefinition = {
  title: 'Song Difficulty',
  heading: 'Difficulty',
  note: 'Higher guess rates mean easier songs. Shares use songs with known difficulty in each group.',
  description: 'guess rates',
  bucketUnit: 'point',
  maximum: 100,
  measurement: summary => summary.difficulty,
  counts: data => data.difficulty,
  formatBucket: String,
  formatMeasurement: value => formatMeasurement('difficulty', value),
};

const LENGTH_DISTRIBUTION: DistributionDefinition = {
  title: 'Song Length',
  heading: 'Length',
  note: 'Middle 50% is the range between the first and third quartiles. Shares use known lengths in each group.',
  description: 'song lengths',
  bucketUnit: 'second',
  measurement: summary => summary.length,
  counts: data => data.length,
  formatBucket: formatDuration,
  formatMeasurement: value => formatMeasurement('length', value),
};

export function difficultyPanel(stats: DatabaseStats, controls: DistributionControls): StatsPanel {
  return distributionPanel(stats, DIFFICULTY_DISTRIBUTION, controls);
}

export function lengthPanel(stats: DatabaseStats, controls: DistributionControls): StatsPanel {
  return distributionPanel(stats, LENGTH_DISTRIBUTION, controls);
}

function distributionPanel(
  stats: DatabaseStats,
  definition: DistributionDefinition,
  { group, bucketSize: size, values, view }: DistributionControls,
): StatsPanel {
  const groups = Object.entries(stats.song_analysis.distributions[group]);
  const shareScale = values === 'share';
  const grouped = group !== 'all';
  const overall = stats.song_analysis.distributions.all.All.summary;
  const known = definition.measurement(overall).known;
  const missing = overall.songs - known;
  const { title, heading } = definition;
  const coverage = 'Known: ' + formatNumber(known) + ' (' + formatShare(known, overall.songs) + ') \u00B7 Missing: '
    + formatNumber(missing) + ' (' + formatShare(missing, overall.songs) + ')';
  const note = definition.note
    + (view !== 'summary' && grouped && shareScale ? ' Stack heights sum the group percentages.' : '');
  if (view === 'summary') {
    return panel(title, [], makeTable(['Group', 'Known songs', 'Mean', 'Median', 'Middle 50%'],
      groups.map(([label, data]) => {
        const measurement = definition.measurement(data.summary);
        return [
          label,
          formatNumber(measurement.known),
          definition.formatMeasurement(measurement.mean),
          definition.formatMeasurement(measurement.median),
          measurement.known
            ? `${definition.formatMeasurement(measurement.q1)}–${definition.formatMeasurement(measurement.q3)}`
            : '\u2014'
        ];
      }), [1, 2, 3, 4]), {}, {
      coverage,
      note
    });
  }
  const maximum = definition.maximum
    ?? Math.max(0, ...groups.flatMap(([, data]) => Object.keys(definition.counts(data)).map(Number)));
  const labels: string[] = [];
  const counts: number[][] = groups.map(() => []);
  const format = definition.formatBucket;
  for (let start = 0; start <= maximum; start += size) {
    const end = Math.min(start + size, maximum + 1);
    labels.push(size === 1 || end - start === 1 ? format(start) : format(start) + '\u2013' + format(end - 1));
    groups.forEach(([, data], index) => {
      let count = 0;
      const histogram = definition.counts(data);
      for (let value = start; value < end; value++) count += histogram[value] || 0;
      counts[index].push(count);
    });
  }
  const series: ChartSeries[] = groups.map(([label, data], index) => {
    const groupKnown = definition.measurement(data.summary).known;
    return {
      label,
      values: counts[index].map(count => {
        if (!shareScale) return count;
        return groupKnown ? count / groupKnown * 100 : null;
      }),
    };
  });
  const rows: ChartRow[] = labels.map((label, index) => [label, series[0]?.values[index] || 0]);
  const table = !groups.length ? makeTable([heading, 'Songs', 'Share'], [], [1, 2])
    : grouped ? makeTable([heading, ...groups.map(([label]) => label)], labels.map((label, index) => [
      label,
      ...series.map(item => {
        const value = item.values[index];
        return value === null ? '\u2014' : shareScale ? percent.format(value) + '%' : formatNumber(value);
      }),
    ]), groups.map((_, index) => index + 1))
      : makeTable(shareScale ? [heading, 'Share', 'Songs'] : [heading, 'Songs', 'Share'], labels.map((label, index) => {
        const count = formatNumber(counts[0][index]);
        const share = formatShare(counts[0][index], known);
        return shareScale ? [label, share, count] : [label, count, share];
      }), [1, 2]);
  return panel(title, rows, table, {
    type: 'bar',
    stacked: grouped,
    series,
    unit: shareScale ? '' : 'songs',
    formatValue: shareScale ? value => percent.format(value) + '%' : undefined,
    labelPrefix: heading + ' ',
    description: 'Distribution of ' + definition.description + ' by ' + group.replaceAll('_', ' ')
      + ', in ' + size + '-' + definition.bucketUnit + ' buckets',
  }, {
    coverage,
    note
  });
}
