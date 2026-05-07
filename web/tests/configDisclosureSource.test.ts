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
  configSource.includes('xl:flex-nowrap xl:gap-2.5'),
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
  false,
  'ChatInterface should not duplicate export theme controls inside the outline toolbar'
);

console.log('configDisclosureSource.test.ts passed');
