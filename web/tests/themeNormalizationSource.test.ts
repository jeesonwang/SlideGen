import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const files = [
  'src/pages/auth/LoginPage.tsx',
  'src/pages/auth/SignupPage.tsx',
  'src/pages/dashboard/DashboardPage.tsx',
];

const forbiddenPatterns = [
  'text-secondary-',
  'border-secondary-',
  'bg-accent-500',
  'text-accent-500',
  'shadow-soft-lg',
  'animate-scale-in',
  'glass-panel',
  'hover:scale-[1.01]',
];

for (const relativePath of files) {
  const content = readFileSync(resolve(relativePath), 'utf8');

  for (const pattern of forbiddenPatterns) {
    assert.equal(
      content.includes(pattern),
      false,
      `${relativePath} should not contain deprecated or undefined style token: ${pattern}`
    );
  }
}

console.log('themeNormalizationSource.test.ts passed');
