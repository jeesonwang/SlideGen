import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const appLayoutSource = readFileSync(
  new URL('../src/components/layout/AppLayout.tsx', import.meta.url),
  'utf8'
);

const sidebarSource = readFileSync(
  new URL('../src/components/common/Sidebar.tsx', import.meta.url),
  'utf8'
);

assert.match(
  appLayoutSource,
  /const\s+\{\s*sidebarCollapsed\s*\}\s*=\s*useUIStore\(\)/,
  'AppLayout should read sidebarCollapsed from the UI store'
);

assert.match(
  appLayoutSource,
  /collapsed=\{sidebarCollapsed\}/,
  'AppLayout should bind the left Sider collapsed state'
);

assert.match(
  appLayoutSource,
  /collapsedWidth=\{96\}/,
  'AppLayout should give the refreshed collapsed sidebar enough width to avoid a cramped vertical capsule'
);

assert.match(
  sidebarSource,
  /const\s+\{[^}]*sidebarCollapsed[^}]*\}\s*=\s*useUIStore\(\)/,
  'Sidebar should read the collapse state from the UI store'
);

assert.match(
  sidebarSource,
  /toggleSidebar/,
  'Sidebar should provide a visible toggleSidebar control'
);

assert.match(
  sidebarSource,
  /aria-label="Toggle sidebar"/,
  'Sidebar should render a visible toggle button for collapsing and expanding'
);

assert.match(
  sidebarSource,
  /sidebarCollapsed\s*\?\s*'justify-center px-3 py-4'/,
  'Collapsed sidebar header should center the toggle button horizontally'
);

assert.doesNotMatch(
  sidebarSource,
  /className="flex h-full bg-transparent p-3 text-text-main"/,
  'Sidebar should not keep the same outer padding in collapsed mode as the expanded layout'
);

assert.match(
  sidebarSource,
  /sidebarCollapsed\s*\?\s*'px-2 py-3'\s*:\s*'p-3'/,
  'Sidebar outer padding should become tighter in collapsed mode so the rail keeps enough usable width'
);

assert.match(
  sidebarSource,
  /'workbench-sidebar-shell flex w-full flex-col overflow-hidden'[\s\S]*sidebarCollapsed\s*\?\s*'rounded-\[1\.5rem\]'\s*:\s*'rounded-\[2rem\]'/,
  'Sidebar shell should use a dedicated collapsed shape instead of reusing the full expanded capsule'
);

assert.match(
  sidebarSource,
  /!\s*sidebarCollapsed\s*&&[\s\S]*brand-mark w-8 h-8 rounded-lg flex items-center justify-center/,
  'Sidebar brand icon should only render in expanded mode'
);

assert.doesNotMatch(
  sidebarSource,
  /sidebarCollapsed\s*\?\s*'flex-col items-center gap-3 px-0 py-4'/,
  'Sidebar toggle should stay on the top row instead of moving below the brand in collapsed mode'
);

assert.match(
  sidebarSource,
  /!\s*sidebarCollapsed\s*&&\s*sortedSessions\.length\s*>\s*0/,
  'Sidebar should hide the recent session list when collapsed'
);

assert.match(
  sidebarSource,
  /title=\{sidebarCollapsed \? 'Expand sidebar' : 'Collapse sidebar'\}/,
  'Sidebar toggle tooltip should use English copy'
);

assert.match(
  sidebarSource,
  /!\s*sidebarCollapsed\s*&&[\s\S]*<h1[^>]*>SlideGen<\/h1>/,
  'Sidebar should only render the SlideGen title in expanded mode'
);

console.log('leftSidebarCollapseSource.test.ts passed');
