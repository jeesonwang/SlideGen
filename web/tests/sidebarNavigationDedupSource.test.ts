import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const sidebarSource = readFileSync(
  new URL('../src/components/common/Sidebar.tsx', import.meta.url),
  'utf8'
);

assert.doesNotMatch(
  sidebarSource,
  /key:\s*'new'\s*,\s*icon:\s*<MessageOutlined\s*\/>\s*,\s*label:\s*'New Presentation'\s*,\s*path:\s*'\/generate'/,
  'Sidebar navigation should not duplicate the primary New Presentation action'
);

console.log('sidebarNavigationDedupSource.test.ts passed');
