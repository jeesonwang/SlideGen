import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(
  resolve('web/src/pages/dashboard/DashboardPage.tsx'),
  'utf8'
);

assert.equal(
  source.includes('session.status !== SessionStatus.DELETED'),
  true,
  'Dashboard should filter deleted sessions before rendering stats and recent items'
);
assert.equal(
  source.includes('session.status !== SessionStatus.ARCHIVED'),
  true,
  'Dashboard should filter archived sessions before rendering stats and recent items'
);
assert.equal(
  source.includes('Total Sessions'),
  false,
  'Dashboard should no longer render a total sessions card'
);
assert.equal(
  source.includes('const recentSessions = visibleSessions.slice(0, 5);'),
  true,
  'Dashboard recent sessions should come from visible sessions only'
);
assert.equal(
  source.includes('const totalSessions = visibleSessions.length;'),
  false,
  'Dashboard should not compute or render a total sessions metric'
);
assert.equal(
  source.includes('const recentSessions = sessionsData?.data.slice(0, 5) || [];'),
  false,
  'Dashboard should not slice unfiltered sessions'
);

console.log('dashboardSessionSource.test.ts passed');
