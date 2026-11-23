export const THEME_OPTIONS = [
  { id: 'classic', label: 'Classic' },
  { id: 'dark', label: 'Dark' },
  { id: 'light', label: 'Light' },
] as const;

export type ThemeId = typeof THEME_OPTIONS[number]['id'];

export function isThemeId(value: unknown): value is ThemeId {
  return THEME_OPTIONS.some(option => option.id === value);
}
