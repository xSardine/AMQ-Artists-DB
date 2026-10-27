export interface LogScrollPosition {
  follow: 'start' | 'end' | null;
  scrollTop: number;
  anchors: { id: string; offset: number }[];
}

export function captureLogScroll(viewport: HTMLElement, follow: boolean, ascending: boolean): LogScrollPosition {
  const distance = ascending
    ? viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight
    : viewport.scrollTop;
  const rect = viewport.getBoundingClientRect();
  const headerHeight = viewport.querySelector('thead')?.getBoundingClientRect().height ?? 0;
  const rows = Array.from(viewport.querySelectorAll<HTMLElement>('tbody tr[data-event-id]'));
  const anchors = rows.filter(row => {
    const rowRect = row.getBoundingClientRect();
    return rowRect.bottom > rect.top + headerHeight && rowRect.top < rect.bottom;
  }).slice(0, 3).map(row => ({
    id: row.dataset['eventId']!,
    offset: row.getBoundingClientRect().top - rect.top,
  }));
  return {
    follow: follow && distance < 48 ? (ascending ? 'end' : 'start') : null,
    scrollTop: viewport.scrollTop,
    anchors,
  };
}

export function restoreLogScroll(viewport: HTMLElement, position: LogScrollPosition): void {
  if (position.follow !== null) {
    viewport.scrollTop = position.follow === 'start' ? 0 : viewport.scrollHeight;
    return;
  }
  const rows = Array.from(viewport.querySelectorAll<HTMLElement>('tbody tr[data-event-id]'));
  for (const anchor of position.anchors) {
    const row = rows.find(candidate => candidate.dataset['eventId'] === anchor.id);
    if (row) {
      const offset = row.getBoundingClientRect().top - viewport.getBoundingClientRect().top;
      viewport.scrollTop += offset - anchor.offset;
      return;
    }
  }
  viewport.scrollTop = position.scrollTop;
}
