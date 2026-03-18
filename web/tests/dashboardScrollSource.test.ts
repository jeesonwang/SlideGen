import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('web/src/pages/dashboard/DashboardPage.tsx'), 'utf8');

assert.equal(
  source.includes('overflow-y-auto'),
  true,
  'DashboardPage should expose a vertical scroll container'
);

console.log('dashboardScrollSource.test.ts passed');
