import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const sidebarSource = readFileSync(
  new URL('../src/components/common/Sidebar.tsx', import.meta.url),
  'utf8'
);

assert.match(
  sidebarSource,
  /placement="rightBottom"/,
  'Sidebar user popover should open to the right so it does not cover Settings'
);

assert.doesNotMatch(
  sidebarSource,
  /placement="topLeft"/,
  'Sidebar user popover should not open upward over the Settings button'
);

console.log('sidebarOverlaySource.test.ts passed');
