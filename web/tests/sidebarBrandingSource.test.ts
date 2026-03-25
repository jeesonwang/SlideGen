import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const sidebarSource = readFileSync(
  new URL('../src/components/common/Sidebar.tsx', import.meta.url),
  'utf8'
);

assert.match(
  sidebarSource,
  />SlideGen</,
  'Sidebar brand title should display SlideGen'
);

assert.doesNotMatch(
  sidebarSource,
  /ENTERPRISE/,
  'Sidebar brand should not display ENTERPRISE'
);

console.log('sidebarBrandingSource.test.ts passed');
