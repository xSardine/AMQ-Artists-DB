/** Fields consumed from /api/database_stats, matching the backend's statistics payload. */
export interface CoverageCount {
  present: number;
  total: number;
}

export interface MeasurementSummary {
  known: number;
  mean: number | null;
  median: number | null;
  q1: number | null;
  q3: number | null;
}

export type MeasurementKind = 'difficulty' | 'length';

export interface SongSummary {
  songs: number;
  anime: number;
  song_types: Record<string, number>;
  media: number;
  difficulty: MeasurementSummary;
  length: MeasurementSummary;
}

export interface SongDistribution {
  summary: SongSummary;
  difficulty: Record<string, number>;
  length: Record<string, number>;
}

export interface PeriodStatistics {
  overall: SongSummary;
  song_type: Record<string, SongSummary>;
  anime_format: Record<string, SongSummary>;
}

export interface AnimeSongStatistics {
  anime: number;
  distribution: Record<string, number>;
  median: number | null;
  p90: number | null;
  maximum: number | null;
  most_songs: {
    name: string;
    songs: number;
    song_types: Record<string, number>;
  }[];
}

export interface CreditRoleStatistics {
  songs_with_ids: number;
  text_without_ids: number;
  no_text_or_ids: number;
  unique_direct_ids: number;
  direct_people: number;
  lineup_only_people: number;
  all_identified_people: number;
  specific_group_lineup_songs: number;
  unspecified_group_lineup_songs: number;
  songs_by_id_count: Record<string, number>;
  missing_ids_by_performance: Record<string, {
    text_without_ids: number;
    no_text_or_ids: number;
  }>;
}

export interface CreditedArtist {
  id: number;
  name: string;
  disambiguation: string | null;
  unique_songs: number;
  anime_count: number;
}

export interface DatabaseStats {
  database_updated_at: string | null;
  total_songs: number;
  total_unique_amq_songs: number;
  total_anime: number;
  total_artists: number;
  total_seasons: number;
  links_by_combination: Record<string, number>;
  songs_by_type: Record<string, number>;
  songs_by_broadcast: Record<string, number>;
  songs_by_performance: Record<string, number>;
  songs_by_anime_type: Record<string, number>;
  missing_data: Record<string, number>;
  original_name_coverage: Record<string, CoverageCount>;
  external_id_coverage: Record<string, CoverageCount>;
  artist_credits: {
    types: Record<string, number>;
    directly_credited: number;
    roster_only: number;
    other_catalog_entries: number;
    role_combinations: Record<string, number>;
    aliases: Record<string, number>;
    groups: {
      total: number;
      by_lineup_type: Record<string, number>;
      by_lineup_count: Record<string, number>;
      lineups_by_type: Record<string, number>;
      nested_groups: number;
    };
    roles: Record<string, CreditRoleStatistics>;
    artists_by_unique_song_count: Record<string, number>;
    most_credited: Record<string, CreditedArtist[]>;
  };
  song_analysis: {
    distributions: Record<string, Record<string, SongDistribution>>;
    seasons: Record<string, PeriodStatistics>;
    years: Record<string, PeriodStatistics>;
    songs_per_anime: Record<string, AnimeSongStatistics>;
    genres: Record<string, SongSummary>;
    tags: Record<string, SongSummary>;
  };
}
