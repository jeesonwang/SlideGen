import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const sidebarSource = readFileSync(
  new URL('../src/components/common/Sidebar.tsx', import.meta.url),
  'utf8'
);

const usesMessageOutlined = sidebarSource.includes('<MessageOutlined');

assert.equal(
  /import\s*\{\s*[\s\S]*\bMessageOutlined\b[\s\S]*\}\s*from '@ant-design\/icons';/.test(sidebarSource),
  usesMessageOutlined,
  'Sidebar should import MessageOutlined whenever the component still renders it'
);

console.log('sidebarMessageIconImportSource.test.ts passed');
