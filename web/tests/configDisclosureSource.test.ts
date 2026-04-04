import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const configSource = readFileSync(resolve('src/components/config/ConfigurationPanel.tsx'), 'utf8');

assert.equal(
  chatSource.includes('ConfigurationPanel'),
  true,
  'ChatInterface should render the inline configuration row near the composer'
);
assert.equal(
  chatSource.includes('border-t border-border/70 pt-4'),
  true,
  'ChatInterface should visually separate fixed inline settings beneath the composer actions'
);
assert.equal(
  configSource.includes('xl:grid xl:grid-cols-[7.5rem_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_11rem]'),
  true,
  'ConfigurationPanel should keep the inline settings on one row for wide viewports'
);
assert.equal(
  configSource.includes('showAdvancedSettings'),
  false,
  'ConfigurationPanel should no longer hide settings behind progressive disclosure'
);
assert.equal(
  configSource.includes('Linked References'),
  false,
  'ConfigurationPanel should focus on generation controls once references live in the composer'
);

for (const label of ['Pages', 'Language', 'Template', 'Format', 'Tone', 'Text Volume', 'Web research']) {
  assert.equal(
    configSource.includes(label),
    ['Pages', 'Language', 'Tone', 'Text Volume', 'Web research'].includes(label),
    `ConfigurationPanel visibility for "${label}" should match the inline composer design`
  );
}

assert.equal(
  chatSource.includes('Select theme'),
  true,
  'ChatInterface should expose a post-generation Select theme action near the assistant outline'
);

console.log('configDisclosureSource.test.ts passed');
