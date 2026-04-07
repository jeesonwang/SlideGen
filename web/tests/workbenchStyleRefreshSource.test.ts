import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const sidebarSource = readFileSync(resolve('src/components/common/Sidebar.tsx'), 'utf8');
const chatSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const dashboardSource = readFileSync(resolve('src/pages/dashboard/DashboardPage.tsx'), 'utf8');
const sessionsSource = readFileSync(resolve('src/pages/sessions/SessionsPage.tsx'), 'utf8');
const filesSource = readFileSync(resolve('src/pages/files/FilesPage.tsx'), 'utf8');

assert.equal(
  sidebarSource.includes('workbench-sidebar-shell'),
  true,
  'Sidebar should adopt the shared workbench shell styling for the refreshed rail layout'
);

assert.equal(
  chatSource.includes('workbench-stage-panel'),
  true,
  'Generation page should use the shared stage panel styling for the main composer card'
);

assert.equal(
  chatSource.includes('workbench-tip-panel'),
  true,
  'Generation page should render the refreshed tip surface above the composer stage'
);

for (const [name, source] of [
  ['DashboardPage', dashboardSource],
  ['SessionsPage', sessionsSource],
  ['FilesPage', filesSource],
] as const) {
  assert.equal(
    source.includes('workbench-page'),
    true,
    `${name} should use the shared workbench page shell`
  );
}

console.log('workbenchStyleRefreshSource.test.ts passed');
