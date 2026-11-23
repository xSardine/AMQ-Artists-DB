/** Move an existing item before or after another; invalid moves leave the caller unchanged. */
export function moveItem<T>(
  items: readonly T[],
  item: T,
  target: T,
  after: boolean,
): T[] | null {
  const sourceIndex = items.indexOf(item);
  if (item === target || sourceIndex < 0 || !items.includes(target)) return null;

  const reordered = [...items];
  reordered.splice(sourceIndex, 1);
  const targetIndex = reordered.indexOf(target) + (after ? 1 : 0);
  reordered.splice(targetIndex, 0, item);
  return reordered;
}
