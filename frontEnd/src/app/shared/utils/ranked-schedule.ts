export interface RankedStatus {
  active: boolean;
  region: string | null;
  remainingSeconds: number;
}

export const RANKED_REGIONS = [
  {
    region: 'Central',
    timeZone: 'Europe/Copenhagen',
    timeZoneLabel: 'CET/CEST',
  },
  {
    region: 'Western',
    timeZone: 'America/Chicago',
    timeZoneLabel: 'CDT/CST',
  },
  {
    region: 'Eastern',
    timeZone: 'Asia/Tokyo',
    timeZoneLabel: 'JST',
  },
] as const;

const RANKED_START_SECONDS = (20 * 60 + 30) * 60;
const RANKED_END_SECONDS = (21 * 60 + 23) * 60;
const REGIONS = RANKED_REGIONS.map(({ timeZone, region }) => ({
  region,
  formatter: new Intl.DateTimeFormat('en-US', {
    timeZone,
    hourCycle: 'h23',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }),
}));

export const RANKED_SCHEDULE_LABEL = [
  `${formatClockTime(RANKED_START_SECONDS)}–${formatClockTime(RANKED_END_SECONDS)}`,
  `(${Math.floor((RANKED_END_SECONDS - RANKED_START_SECONDS) / 60)} minutes)`,
].join(' ');

export function getRankedStatus(date: Date = new Date()): RankedStatus {
  for (const { region, formatter } of REGIONS) {
    const parts = formatter.formatToParts(date);
    const part = (type: Intl.DateTimeFormatPartTypes) =>
      Number(parts.find(item => item.type === type)?.value ?? 0);
    const seconds = part('hour') * 3600 + part('minute') * 60 + part('second');
    if (seconds >= RANKED_START_SECONDS && seconds < RANKED_END_SECONDS) {
      return { active: true, region, remainingSeconds: RANKED_END_SECONDS - seconds };
    }
  }
  return { active: false, region: null, remainingSeconds: 0 };
}

export function formatRankedRemaining(status: RankedStatus): string {
  if (!status.active) return '';
  const minutes = Math.floor(status.remainingSeconds / 60);
  const seconds = status.remainingSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function formatClockTime(seconds: number): string {
  const hour = Math.floor(seconds / 3600);
  const minute = Math.floor((seconds % 3600) / 60);
  const period = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
}
