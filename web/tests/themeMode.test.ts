import assert from 'node:assert/strict';
import {
  getThemeModeLabel,
  resolveThemeMode,
  type ResolvedTheme,
  type ThemeMode,
} from '../src/theme/themeMode.ts';

const cases: Array<{
  mode: ThemeMode;
  systemPrefersDark?: boolean;
  expected: ResolvedTheme;
}> = [
  { mode: 'light', systemPrefersDark: true, expected: 'light' },
  { mode: 'dark', systemPrefersDark: false, expected: 'dark' },
  { mode: 'system', systemPrefersDark: true, expected: 'dark' },
  { mode: 'system', systemPrefersDark: false, expected: 'light' },
  { mode: 'system', expected: 'dark' },
];

for (const testCase of cases) {
  assert.equal(
    resolveThemeMode(testCase.mode, testCase.systemPrefersDark),
    testCase.expected,
    `resolveThemeMode(${testCase.mode}, ${String(testCase.systemPrefersDark)}) should be ${testCase.expected}`
  );
}

assert.equal(getThemeModeLabel('light'), 'Light');
assert.equal(getThemeModeLabel('dark'), 'Dark');
assert.equal(getThemeModeLabel('system'), 'System');

console.log('themeMode.test.ts passed');
