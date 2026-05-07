import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(
  resolve('src/pages/dashboard/DashboardPage.tsx'),
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
  source.includes("import { useMemo } from 'react';"),
  true,
  'Dashboard should import useMemo for render-derived session data'
);
assert.match(
  source,
  /const visibleSessions = useMemo\(\s*\(\) =>[\s\S]*sessionsData\?\.data\.filter[\s\S]*,\s*\[sessionsData\?\.data\]\s*\);/,
  'Dashboard should memoize visible sessions from API data'
);
assert.match(
  source,
  /const recentSessions = useMemo\(\s*\(\) => visibleSessions\.slice\(0,\s*5\),\s*\[visibleSessions\]\s*\);/,
  'Dashboard recent sessions should be memoized from visible sessions only'
);
assert.match(
  source,
  /const activeSessions = useMemo\(\s*\(\) =>[\s\S]*visibleSessions\.filter[\s\S]*session\.status === SessionStatus\.ACTIVE[\s\S]*,\s*\[visibleSessions\]\s*\);/,
  'Dashboard should memoize active sessions from visible sessions'
);
assert.match(
  source,
  /const latestSession = useMemo\(\s*\(\) => activeSessions\[0\] \|\| visibleSessions\[0\],\s*\[activeSessions,\s*visibleSessions\]\s*\);/,
  'Dashboard should memoize the latest session selection'
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
