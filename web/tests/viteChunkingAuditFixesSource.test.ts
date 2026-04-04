import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const viteConfigSource = readFileSync(resolve('vite.config.ts'), 'utf8');

assert.equal(
  viteConfigSource.includes("return 'antd-vendor';"),
  false,
  'vite manualChunks should not force all Ant Design modules into a single antd-vendor chunk'
);

assert.equal(
  viteConfigSource.includes("return 'antd-rc-vendor';"),
  false,
  'vite manualChunks should not force all rc-* modules into a single antd-rc-vendor chunk'
);

console.log('viteChunkingAuditFixesSource.test.ts passed');
