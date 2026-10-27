import type { RecordDescription } from './contribution-types';

export function songTypeLabel(type: number, number: number): string {
  switch (type) {
    case 1: return `OP${number}`;
    case 2: return `ED${number}`;
    case 3: return 'IN';
    default: return 'Unknown';
  }
}

export function recordContext(target: RecordDescription, includeArtistType = false): string {
  const artistId = target.locator?.artist_id;
  if (artistId !== undefined) {
    const artistType = includeArtistType && target.type
      ? target.type.charAt(0).toUpperCase() + target.type.slice(1)
      : '';
    return [`Artist #${artistId}`, artistType, target.disambiguation].filter(Boolean).join(' \u00B7 ');
  }
  if (target.song_type !== undefined && target.song_number !== undefined) {
    const anime = target.anime_label || target.detail.split(' \u00B7 ')[0];
    return `${anime} · ${songTypeLabel(target.song_type, target.song_number)}`;
  }
  return target.detail;
}

export function displayValue(value: unknown): string {
  if (Array.isArray(value)) return value.join('\n') || 'Not filled';
  if (typeof value === 'string' || typeof value === 'number') return String(value);
  return 'Not filled';
}
