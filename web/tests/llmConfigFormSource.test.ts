import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const llmFormSource = readFileSync(
  resolve('src/components/config/LLMConfigForm.tsx'),
  'utf8'
);

assert.equal(
  llmFormSource.includes("mode={modelsData?.models.length ? undefined : 'tags'}"),
  false,
  'LLMConfigForm should not use tags mode for model_id because the API expects a string'
);

assert.match(
  llmFormSource,
  /Fetch Models/,
  'LLMConfigForm should expose a fetch-models action for loading provider models dynamically'
);

assert.equal(
  llmFormSource.includes('useLLMModels'),
  false,
  'LLMConfigForm should not rely on preset provider model lists'
);

assert.match(
  llmFormSource,
  /availableModels\.length > 0[\s\S]*<Input[\s\S]*placeholder="Enter a model ID"/,
  'LLMConfigForm should keep manual model ID entry as the fallback when no fetched models are available'
);

console.log('llmConfigFormSource.test.ts passed');
