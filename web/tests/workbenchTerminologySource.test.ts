import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const sidebarSource = readFileSync(resolve('src/components/common/Sidebar.tsx'), 'utf8');
const chatSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const composerSource = readFileSync(resolve('src/components/chat/ComposerCard.tsx'), 'utf8');
const chatMessageSource = readFileSync(resolve('src/components/chat/ChatMessageItem.tsx'), 'utf8');
const dashboardSource = readFileSync(resolve('src/pages/dashboard/DashboardPage.tsx'), 'utf8');
const sessionsSource = readFileSync(resolve('src/pages/sessions/SessionsPage.tsx'), 'utf8');
const filesSource = readFileSync(resolve('src/pages/files/FilesPage.tsx'), 'utf8');
const routerSource = readFileSync(resolve('src/router.tsx'), 'utf8');

assert.equal(
  sidebarSource.includes('Recent Chats'),
  false,
  'Sidebar should stop using chat-centric recent history terminology'
);
assert.equal(
  sidebarSource.includes('New Chat'),
  false,
  'Sidebar primary action should be renamed for presentation work'
);
assert.equal(
  sidebarSource.includes('Projects'),
  true,
  'Sidebar should expose a projects entry point'
);
assert.equal(
  sidebarSource.includes('Reference Library'),
  false,
  'Sidebar should not expose references as a top-level workspace entry point'
);
assert.equal(
  dashboardSource.includes("navigate('/knowledge-base')"),
  false,
  'Dashboard should keep reference uploads inside the generation workspace instead of linking to a library page'
);
assert.equal(
  routerSource.includes("path: 'knowledge-base'"),
  false,
  'Reference library should not remain a directly routed workspace section'
);

assert.equal(
  chatSource.includes('Reset Chat'),
  false,
  'Generation workspace should stop using reset chat language'
);
assert.equal(
  chatSource.includes('Start a conversation to create your presentation'),
  false,
  'Generation empty state should frame the task as presentation creation work'
);
assert.equal(
  composerSource.includes('Upload references'),
  true,
  'Generation workspace should describe uploaded files as reference materials'
);

assert.equal(
  dashboardSource.includes('Quick Actions'),
  false,
  'Dashboard should no longer present the homepage as a generic quick actions panel'
);
assert.equal(
  dashboardSource.includes('Continue recent work'),
  true,
  'Dashboard should foreground continuing recent projects'
);

assert.equal(
  sessionsSource.includes('<Title level={2}') && sessionsSource.includes('Projects'),
  true,
  'Projects page should use project terminology in the main heading'
);

assert.equal(
  filesSource.includes('Knowledge Base'),
  false,
  'Files page should stop using knowledge base as the top-level page title'
);
assert.equal(
  filesSource.includes('Reference Library'),
  true,
  'Files page should be presented as a reference library'
);

for (const [name, source] of [
  ['Sidebar', sidebarSource],
  ['ChatInterface', chatSource],
  ['ComposerCard', composerSource],
  ['ChatMessageItem', chatMessageSource],
  ['DashboardPage', dashboardSource],
  ['SessionsPage', sessionsSource],
  ['FilesPage', filesSource],
  ['router', routerSource],
] as const) {
  assert.equal(
    /[\p{Script=Han}]/u.test(source),
    false,
    `${name} should keep display copy in English`
  );
}

console.log('workbenchTerminologySource.test.ts passed');
