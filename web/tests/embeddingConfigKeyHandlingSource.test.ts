import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const helperSource = readFileSync(
  resolve('web/src/pages/config/embeddingConfigKeyHandling.ts'),
  'utf8'
);
const pageSource = readFileSync(
  resolve('web/src/pages/config/EmbeddingConfigPage.tsx'),
  'utf8'
);

assert.match(
  helperSource,
  /value!\.startsWith\('\*\*\*'\)/,
  'Embedding key helper should recognize masked API keys'
);

assert.match(
  helperSource,
  /config_id: config\.id/,
  'Testing a saved embedding config should include config_id so the backend can look up the stored secret'
);

assert.match(
  helperSource,
  /api_key: isMaskedApiKey\(config\.api_key\) \? undefined : config\.api_key \|\| undefined/,
  'Testing a saved embedding config should omit masked API keys from the payload'
);

assert.match(
  helperSource,
  /if \(values\.api_key === initialValues\?\.api_key\)[\s\S]*api_key: undefined/,
  'Submitting an unchanged masked embedding API key should omit api_key so the backend can keep the stored secret'
);

assert.match(
  pageSource,
  /testMutation\.mutateAsync\(buildEmbeddingConfigTestPayload\(config\)\)/,
  'EmbeddingConfigPage should build test payloads through the key-handling helper'
);

assert.match(
  pageSource,
  /data: sanitizeEmbeddingConfigSubmitValues\(values, editingConfig\)/,
  'EmbeddingConfigPage should sanitize update payloads before sending them to the backend'
);

console.log('embeddingConfigKeyHandlingSource.test.ts passed');
