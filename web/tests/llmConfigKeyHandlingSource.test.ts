import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const helperSource = readFileSync(
  resolve('web/src/pages/config/llmConfigKeyHandling.ts'),
  'utf8'
);
const pageSource = readFileSync(
  resolve('web/src/pages/config/LLMConfigPage.tsx'),
  'utf8'
);

assert.match(
  helperSource,
  /value!\.startsWith\('\*\*\*'\)/,
  'LLM key helper should recognize masked API keys'
);

assert.match(
  helperSource,
  /config_id: config\.id/,
  'Testing a saved config should include config_id so the backend can look up the stored secret'
);

assert.match(
  helperSource,
  /api_key: isMaskedApiKey\(config\.api_key\) \? undefined : config\.api_key \|\| undefined/,
  'Testing a saved config should omit masked API keys from the payload'
);

assert.match(
  helperSource,
  /if \(values\.api_key === initialValues\?\.api_key\)[\s\S]*api_key: undefined/,
  'Submitting an unchanged masked API key should omit api_key so the backend can keep the stored secret'
);

assert.match(
  pageSource,
  /testMutation\.mutateAsync\(buildLLMConfigTestPayload\(config\)\)/,
  'LLMConfigPage should build test payloads through the key-handling helper'
);

assert.match(
  pageSource,
  /data: sanitizeLLMConfigSubmitValues\(values, editingConfig\)/,
  'LLMConfigPage should sanitize update payloads before sending them to the backend'
);

console.log('llmConfigKeyHandlingSource.test.ts passed');
