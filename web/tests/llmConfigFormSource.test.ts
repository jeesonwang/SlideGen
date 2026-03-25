import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const llmFormSource = readFileSync(
  resolve('web/src/components/config/LLMConfigForm.tsx'),
  'utf8'
);

assert.equal(
  llmFormSource.includes("mode={modelsData?.models.length ? undefined : 'tags'}"),
  false,
  'LLMConfigForm should not use tags mode for model_id because the API expects a string'
);

assert.match(
  llmFormSource,
  /modelsData\?\.models\.length[\s\S]*<Input[\s\S]*placeholder="Enter a model ID"/,
  'LLMConfigForm should render a plain text input when the provider has no preset models'
);

console.log('llmConfigFormSource.test.ts passed');
