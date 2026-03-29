import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const embeddingFormSource = readFileSync(
  resolve('src/components/config/EmbeddingConfigForm.tsx'),
  'utf8'
);

assert.match(
  embeddingFormSource,
  /Fetch Models/,
  'EmbeddingConfigForm should expose a fetch-models action for loading provider models dynamically'
);

assert.equal(
  embeddingFormSource.includes('useEmbeddingModels'),
  false,
  'EmbeddingConfigForm should not rely on preset provider model lists'
);

assert.match(
  embeddingFormSource,
  /availableModels\.length > 0[\s\S]*<Input[\s\S]*placeholder="Enter a model ID"/,
  'EmbeddingConfigForm should keep manual model ID entry as the fallback when no fetched models are available'
);

console.log('embeddingConfigFormSource.test.ts passed');
