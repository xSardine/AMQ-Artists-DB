import type { SongCredit, Song } from '../songs/song';

export type CreditSearchRole = 'artist' | 'composer';

type CreditSection = {
  title: string;
  people: SongCredit[];
  role: CreditSearchRole;
};

export function collectPersonIds(
  people: SongCredit | readonly SongCredit[] | null | undefined,
): number[] {
  const entries: readonly SongCredit[] = Array.isArray(people)
    ? people
    : people ? [people as SongCredit] : [];
  return entries.map((person) => person.id);
}

export function buildCreditSections(song: Song): CreditSection[] {
  const sections: CreditSection[] = [
    // Artist entries commonly contain aliases, group memberships, and lineups.
    // Put simpler cards first so cards of similar height tend to share a grid
    // row, reducing empty space. Composer and arranger entries are normally
    // flat, so their backend order is preserved.
    { title: 'Artists', people: packArtistCardsByDetailCount(song.artists), role: 'artist' },
    { title: 'Composers', people: song.composers, role: 'composer' },
    { title: 'Arrangers', people: song.arrangers, role: 'composer' },
  ];
  return sections.filter((section) => section.people.length > 0);
}

function packArtistCardsByDetailCount(artists: readonly SongCredit[]): SongCredit[] {
  return [...artists].sort(
    (left, right) => artistCardDetailCount(left) - artistCardDetailCount(right),
  );
}

function artistCardDetailCount(person: SongCredit): number {
  return (
    Math.max(0, (person.names?.length ?? 0) - 1) +
    (person.groups?.length ?? 0) +
    (person.members?.length ?? 0)
  );
}

export function creditSearchTitle(
  role: CreditSearchRole,
  scope: 'primary' | 'member' | 'group',
): string {
  const verb = role === 'artist' ? 'sung by' : 'composed by';
  const subject = scope === 'primary'
    ? role === 'artist' ? 'this artist' : 'this composer'
    : scope === 'member' ? 'this member' : 'this group';
  return `Search songs ${verb} ${subject}`;
}
