import type { DatabaseStats, MeasurementKind, MeasurementSummary, SongSummary } from './stats-types';
import type { StatsTable } from './stats-table.component';
const number = new Intl.NumberFormat('en-US');
const percent = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }); const compareNames = new Intl.Collator('en', {
  sensitivity: 'base',
  numeric: true
}).compare;

export type LabelView = 'counts' | 'types' | 'coverage' | MeasurementKind;

type LabelColumn = [
  key: string,
  label: string,
  value: (data: SongSummary) => number | null,
  format: (value: number, data: SongSummary) => string
];
export const formatNumber = (value: number) => number.format(value);

export function makeTable(
  headings: string[],
  rows: string[][],
  numericColumns: number[] = [],
): StatsTable {
  return {
    headings,
    rows,
    numericColumns
  };
}

export function formatDuration(seconds: number) {
  seconds = Math.round(seconds);
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${String(remainder).padStart(2, '0')}`;
}

export function friendlyLabel(key: string) {
  return key
    .replace(/^songs_without_/, 'Songs without ')
    .replace(/^anime_without_/, 'Anime without ')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatShare(value: number, total: number | undefined, formatter = percent) {
  return total ? `${formatter.format(value / total * 100)}%` : '\u2014';
}

export function formatMeasurement(kind: MeasurementKind, value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '\u2014';
  }
  return kind === 'length' ? formatDuration(value) : `${percent.format(value)}%`;
}

export function formatRange(kind: MeasurementKind, measurement: MeasurementSummary) {
  return measurement.known ? `${formatMeasurement(kind, measurement.q1)}–${formatMeasurement(kind, measurement.q3)}` : '\u2014';
}
const creditRoles: Record<string, string> = {
  performer: 'Performer',
  composer: 'Composer',
  arranger: 'Arranger'
};

export function artistTable(stats: DatabaseStats, view: string) {
  const data = stats.artist_credits;
  const totalArtists = stats.total_artists;
  let headings, rows, note;
  if (view === 'overview') {
    headings = ['Type', 'IDs', 'Share'];
    rows = Object.entries(data.types).map(([label, count]) => [label, number.format(count), formatShare(count, totalArtists)]);
    note = `${number.format(data.directly_credited)} IDs have direct song credits; `
      + `${number.format(data.roster_only)} appear only in rosters; `
      + `${number.format(data.other_catalog_entries)} have neither.`;
  } else if (view === 'roles') {
    headings = ['Role combination', 'IDs', 'Share'];
    const total = Object.values(data.role_combinations).reduce((sum, count) => sum + count, 0);
    rows = Object.entries(data.role_combinations).map(([label, count]) => [label, number.format(count), formatShare(count, total)]);
    note = 'Each directly credited ID appears in one combination. Roster members are excluded.';
  } else if (view === 'aliases') {
    headings = ['Metric', 'Count'];
    rows = [
      ['Regular aliases', 'total_aliases'],
      ['Distinct names', 'distinct_names'],
      ['IDs with multiple aliases', 'artists_with_multiple_aliases'],
      ['Names shared across IDs', 'shared_names'],
      ['IDs sharing names', 'artists_with_shared_names'],
      ['IDs with disambiguation', 'artists_with_disambiguation']
    ].map(([label, key]) => [label, number.format(data.aliases[key])]);
    note = 'Original aliases are excluded. Shared-name comparisons ignore case; matching names can belong to different people or groups.';
  } else if (view === 'groups' || view === 'lineups') {
    headings = [view === 'groups' ? 'Recorded lineups' : 'Lineups per group', 'Groups', 'Share'];
    const groups = data.groups;
    const values = view === 'groups' ? groups.by_lineup_type : groups.by_lineup_count;
    rows = Object.entries(values).map(([label, count]) => [label, number.format(count), formatShare(count, groups.total)]);
    note = `Includes choirs. ${number.format(groups.lineups_by_type.Vocalists)} vocalist lineups, `
      + `${number.format(groups.lineups_by_type.Composers)} composer lineups; `
      + `${number.format(groups.nested_groups)} groups contain another group in a roster.`;
  } else {
    headings = ['Unique AMQ songs', 'Artist IDs', 'Share'];
    const values = data.artists_by_unique_song_count;
    const total = Object.values(values).reduce((sum, count) => sum + count, 0);
    rows = Object.entries(values).map(([label, count]) => [label, number.format(count), formatShare(count, total)]);
    note = 'Directly credited IDs across all roles. Repeated uses and multiple roles on the same song count once; 0 means no positive AMQ song ID.';
  }
  return {
    table: makeTable(headings, rows, [1, 2]),
    note
  };
}

export function creditTable(stats: DatabaseStats, view: string) {
  const roles = stats.artist_credits.roles;
  let headings, rows, note;
  let numericColumns = [1, 2, 3, 4];
  if (view === 'coverage') {
    headings = ['Role', 'With IDs', 'Text only', 'No credit', 'Unique IDs'];
    rows = Object.entries(creditRoles).map(([role, label]) => {
      const data = roles[role];
      return [
        label,
        number.format(data.songs_with_ids),
        number.format(data.text_without_ids),
        number.format(data.no_text_or_ids),
        number.format(data.unique_direct_ids)
      ];
    });
    note = 'Song counts. With IDs means at least one direct credit ID; ' + 'text only means a credit name without IDs; no credit means neither. '
      + 'Unique IDs counts identities per role.';
  } else if (view === 'missing') {
    headings = ['Role', 'Performance', 'Text only', 'No credit'];
    numericColumns = [2, 3];
    rows = Object.entries(creditRoles).flatMap(([role, label]) => Object.entries(roles[role].missing_ids_by_performance).map(([performance, gap]) => [
      label,
      performance,
      number.format(gap.text_without_ids),
      number.format(gap.no_text_or_ids)
    ])
    );
    note = 'Songs without IDs, grouped by performance. Instrumental songs can legitimately have no performer ID.';
  } else if (view === 'people') {
    headings = ['Role', 'Direct', 'Lineup only', 'Total people'];
    rows = Object.entries(creditRoles).map(([role, label]) => {
      const data = roles[role];
      return [
        label,
        number.format(data.direct_people),
        number.format(data.lineup_only_people),
        number.format(data.all_identified_people)
      ];
    });
    note = 'Distinct people identified by direct credits or specific lineups, including nested rosters. Unspecified group lineups are not expanded.';
  } else if (view === 'groups') {
    headings = ['Role', 'With lineup', 'Unspecified'];
    rows = Object.entries(creditRoles).map(([role, label]) => [
      label,
      number.format(roles[role].specific_group_lineup_songs),
      number.format(roles[role].unspecified_group_lineup_songs)
    ]);
    note = 'Songs with a group or choir credit. Columns can overlap when a song credits both a specific and an unspecified lineup.';
  } else {
    headings = ['IDs per song', ...Object.values(creditRoles)];
    rows = Object.keys(roles.performer.songs_by_id_count).map((bucket) => [
      bucket,
      ...Object.keys(creditRoles).map((role) => number.format(roles[role].songs_by_id_count[bucket]))
    ]);
    note = 'Distinct directly credited IDs per song. One group ID can represent many people.';
  }
  return {
    table: makeTable(headings, rows, numericColumns),
    note
  };
}

export function rankingTable(stats: DatabaseStats, role: string) {
  const rows = stats.artist_credits.most_credited[role].map((artist) => [
    number.format(artist.id),
    artist.name + (artist.disambiguation ? ` (${artist.disambiguation})` : ''),
    number.format(artist.unique_songs),
    number.format(artist.anime_count)
  ]);
  return makeTable(['ID', 'Artist', 'Unique songs', 'Anime'], rows, [0, 2, 3]);
}

export function labelTable(
  stats: DatabaseStats,
  kind: 'genre' | 'tag',
  view: LabelView,
  query: string,
  requestedSort: string,
) {
  const entries = Object.entries(stats.song_analysis[kind === 'genre' ? 'genres' : 'tags']);
  const totalSongs = stats.total_songs;
  const columns: LabelColumn[] = view === 'counts' ? [
    ['anime', 'Anime', (data) => data.anime, number.format],
    ['songs', 'Songs', (data) => data.songs, number.format],
    [
      'share',
      'Share',
      (data) => data.songs / (totalSongs || 1) * 100,
      (value) => `${percent.format(value)}%`
    ],
    ['density', 'Songs/anime', (data) => data.songs / (data.anime || 1), percent.format]
  ] : view === 'types' ? [
    ...['Opening', 'Ending', 'Insert'].map<LabelColumn>((type) => [
      type,
      `${type} %`,
      (data) => data.song_types[type] / (data.songs || 1) * 100,
      (value) => `${percent.format(value)}%`
    ])
  ] : view === 'coverage' ? [
    ...(['difficulty', 'length', 'media'] as const).map<LabelColumn>((key) => [
      key,
      `${friendlyLabel(key)} %`,
      (data) => (key === 'media' ? data.media : data[key].known) / (data.songs || 1) * 100,
      (value) => `${percent.format(value)}%`
    ])
  ] : [
    ['known', 'Known songs', (data) => data[view].known, number.format],
    ['mean', 'Mean', (data) => data[view].mean, (value) => formatMeasurement(view, value)],
    ['median', 'Median', (data) => data[view].median, (value) => formatMeasurement(view, value)],
    ['range', 'Middle 50%', (data) => data[view].q3, (_, data) => formatRange(view, data[view])]
  ];
  const choices = [
    ['count', 'Most songs'],
    ['name', 'A\u2013Z'],
    ...columns
      .filter(([key]) => !['songs', 'share', 'range'].includes(key))
      .map(([key, label]) => [key, label])
  ];
  const sortKey = choices.some(([key]) => key === requestedSort) ? requestedSort : 'count';
  const sortColumn = columns.find(([key]) => key === sortKey);
  const sortValue = (data: SongSummary) => sortColumn ? sortColumn[2](data) ?? -Infinity : data.songs;
  const filtered = entries.filter(([label]) => label.toLowerCase().includes(query));
  filtered.sort(([nameA, dataA], [nameB, dataB]) => (sortKey === 'name' ? 0 : sortValue(dataB) - sortValue(dataA)) || compareNames(nameA, nameB));
  const rows = filtered.map(([label, data]) => [
    label,
    ...columns.map(([, , value, format]) => {
      const amount = value(data);
      return amount === null ? '\u2014' : format(amount, data);
    })
  ]);
  return {
    table: makeTable([kind === 'genre' ? 'Genre' : 'Tag', ...columns.map(([, name]) => name)], rows, columns.map((_, index) => index + 1)),
    sortOptions: choices,
    sortKey,
    kicker: String(filtered.length) + (query ? ' / ' + entries.length : '') + (kind === 'genre' ? ' genres' : ' tags')
  };
}
