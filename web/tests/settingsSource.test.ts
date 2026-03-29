import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const settingsSource = readFileSync(resolve('src/pages/settings/SettingsPage.tsx'), 'utf8');
const llmSource = readFileSync(resolve('src/pages/config/LLMConfigPage.tsx'), 'utf8');
const embeddingSource = readFileSync(resolve('src/pages/config/EmbeddingConfigPage.tsx'), 'utf8');

assert.equal(
  settingsSource.includes('overflow-y-auto'),
  true,
  'SettingsPage should expose a vertical scroll container'
);

const sources = [
  ['SettingsPage', settingsSource],
  ['LLMConfigPage', llmSource],
  ['EmbeddingConfigPage', embeddingSource],
] as const;

for (const [name, source] of sources) {
  assert.equal(
    /[\p{Script=Han}]/u.test(source),
    false,
    `${name} should not contain Chinese copy`
  );
}

console.log('settingsSource.test.ts passed');
