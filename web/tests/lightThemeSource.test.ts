import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const files = [
  'web/src/pages/dashboard/DashboardPage.tsx',
  'web/src/components/common/Sidebar.tsx',
  'web/src/pages/sessions/SessionsPage.tsx',
  'web/src/components/sessions/SessionList.tsx',
  'web/src/pages/config/LLMConfigPage.tsx',
  'web/src/pages/config/EmbeddingConfigPage.tsx',
];

const forbiddenPatterns = [
  'text-slate-',
  'bg-white/5',
  'bg-white/10',
  'border-white/10',
  'border-white/5',
  '!text-slate-',
];

for (const relativePath of files) {
  const content = readFileSync(resolve(relativePath), 'utf8');

  for (const pattern of forbiddenPatterns) {
    assert.equal(
      content.includes(pattern),
      false,
      `${relativePath} should not contain hard-coded dark theme token: ${pattern}`
    );
  }
}

console.log('lightThemeSource.test.ts passed');
