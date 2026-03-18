export type ThemeMode = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

export const THEME_MODE_OPTIONS: Array<{
  value: ThemeMode;
  label: string;
}> = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
];

export const resolveThemeMode = (
  mode: ThemeMode,
  systemPrefersDark?: boolean
): ResolvedTheme => {
  if (mode === 'light' || mode === 'dark') {
    return mode;
  }

  return systemPrefersDark === false ? 'light' : 'dark';
};

export const getThemeModeLabel = (mode: ThemeMode): string =>
  THEME_MODE_OPTIONS.find((option) => option.value === mode)?.label ?? 'System';
