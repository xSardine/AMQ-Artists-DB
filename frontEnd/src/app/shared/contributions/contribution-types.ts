import type { ContributionField } from './contribution-fields';

export type TargetKind = 'anime' | 'artist' | 'song';

export type RecordArtistType = 'person' | 'group' | 'choir';

export interface RecordDescription {
  label: string;
  detail: string;
  type?: RecordArtistType;
  disambiguation?: string | null;
  locator?: {
    artist_id?: number;
    ann_song_id?: number | null;
  };
  anime_label?: string;
  song_type?: number;
  song_number?: number;
}

export type ContributionOperation = 'set' | 'clear' | 'add_alias' | 'replace_alias' | 'remove_alias';

export type ContributionValue = string | string[] | number | null;

export interface ContributionPayload {
  value: string | number | null;
  old_value: string | null;
}

export interface ContributionTarget extends RecordDescription {
  id: string;
  kind: TargetKind;
  values: Partial<Record<ContributionField, ContributionValue>>;
  versions: Partial<Record<ContributionField, number>>;
}

export interface ProposedChange {
  target_id: string;
  field: ContributionField;
  operation: ContributionOperation;
  payload: ContributionPayload;
  base_revision: number;
  label: string;
}

export type ReviewAction = '' | 'approve' | 'reject' | 'hold' | 'duplicate';

export interface ReviewEvent {
  id: number;
  reviewer_name: string;
  action: string;
  comment: string;
  created_at: string;
  reviewed_value: ContributionPayload | null;
}

export interface ReviewChange {
  id: number;
  target_id: string;
  field: ContributionField;
  operation: ContributionOperation;
  proposed_value: ContributionPayload;
  reviewed_value: ContributionPayload;
  review_status: string;
  review_version: number;
  target: RecordDescription;
  active_value: ContributionValue;
  planned_value: ContributionValue;
  field_revision: number;
  latest_approved_revision: number;
  conflict: string | null;
  warnings: string[];
  event_count: number;
}

export interface ReviewSummary {
  id: number;
  contributor_name: string;
  comment: string;
  submitted_at: string;
  change_count: number;
}

export interface ReviewSubmission extends ReviewSummary {
  changes: ReviewChange[];
}

export interface ReviewIssue {
  approved_revision: number;
  target: RecordDescription;
  reason: string;
}

export interface ReviewQueue {
  submissions: ReviewSummary[];
  next_before: number | null;
  counts: Record<string, number>;
  loaded_revision: number;
  latest_revision: number;
  waiting_for_restart: number;
  issue_count: number;
}

export interface ReviewHistoryPage {
  events: ReviewEvent[];
  total: number;
}

export interface ReviewIssuePage {
  issues: ReviewIssue[];
  total: number;
}
