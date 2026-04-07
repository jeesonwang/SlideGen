import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const sidebarSource = readFileSync(
  new URL('../src/components/common/Sidebar.tsx', import.meta.url),
  'utf8'
);

assert.match(
  sidebarSource,
  /key:\s*'projects'[\s\S]*icon:\s*<FileOutlined\s*\/>/,
  'Projects should keep the document-style navigation icon'
);

assert.match(
  sidebarSource,
  /key:\s*'knowledge-base'[\s\S]*icon:\s*<BookOutlined\s*\/>/,
  'Reference Library should use a distinct library-style icon'
);

console.log('sidebarDistinctNavIconsSource.test.ts passed');
