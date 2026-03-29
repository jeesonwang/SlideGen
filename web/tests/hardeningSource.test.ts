import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const topicInputSource = readFileSync(
  resolve('src/components/generation/TopicInput.tsx'),
  'utf8'
);
const configurationPanelSource = readFileSync(
  resolve('src/components/config/ConfigurationPanel.tsx'),
  'utf8'
);
const sidebarSource = readFileSync(
  resolve('src/components/common/Sidebar.tsx'),
  'utf8'
);
const llmListSource = readFileSync(
  resolve('src/components/config/LLMConfigList.tsx'),
  'utf8'
);
const embeddingListSource = readFileSync(
  resolve('src/components/config/EmbeddingConfigList.tsx'),
  'utf8'
);

assert.match(
  topicInputSource,
  /<button[\s\S]*aria-pressed=\{isSelected\}/,
  'TemplateSelector should expose each template card as a real toggle button'
);

assert.match(
  configurationPanelSource,
  /<Radio\.Group[\s\S]*value=\{exportFormat\}/,
  'ConfigurationPanel should use an accessible Radio.Group for export format'
);

assert.match(
  sidebarSource,
  /<button[\s\S]*aria-current=\{currentSessionId === session\.id \? 'page' : undefined\}/,
  'Recent session entries should be rendered as buttons with current-state semantics'
);

for (const [name, source] of [
  ['LLMConfigList', llmListSource],
  ['EmbeddingConfigList', embeddingListSource],
] as const) {
  assert.match(
    source,
    /maskSecret\(/,
    `${name} should mask API keys before rendering them`
  );

  assert.doesNotMatch(
    source,
    /<Text code>\{config\.api_key\}<\/Text>/,
    `${name} should not render raw API keys in the UI`
  );
}

console.log('hardeningSource.test.ts passed');
