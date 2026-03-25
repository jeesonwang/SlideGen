import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const embeddingListSource = readFileSync(
  resolve('web/src/components/config/EmbeddingConfigList.tsx'),
  'utf8'
);
const llmListSource = readFileSync(
  resolve('web/src/components/config/LLMConfigList.tsx'),
  'utf8'
);

for (const [name, source] of [
  ['EmbeddingConfigList', embeddingListSource],
  ['LLMConfigList', llmListSource],
] as const) {
  assert.equal(
    source.includes('flex flex-col gap-2 min-w-0'),
    true,
    `${name} should render the card header as two stacked rows`
  );

  assert.equal(
    source.includes('flex flex-wrap items-center gap-2'),
    true,
    `${name} should keep status tags together in a dedicated second row`
  );

  assert.equal(
    source.includes("whiteSpace: 'normal'"),
    true,
    `${name} should disable single-line truncation in the Ant Design card title area`
  );
}

console.log('configCardHeaderLayoutSource.test.ts passed');
