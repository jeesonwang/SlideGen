import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const constantsSource = readFileSync(
  new URL('../src/utils/constants.ts', import.meta.url),
  'utf8'
);

assert.match(
  constantsSource,
  /LLM_CONFIG:\s*{[\s\S]*LIST:\s*'\/api\/v1\/llm-config\/'/,
  'LLM config list endpoint should include a trailing slash to avoid FastAPI redirects'
);

assert.match(
  constantsSource,
  /LLM_CONFIG:\s*{[\s\S]*CREATE:\s*'\/api\/v1\/llm-config\/'/,
  'LLM config create endpoint should include a trailing slash to match the backend route'
);

assert.match(
  constantsSource,
  /LLM_CONFIG:\s*{[\s\S]*FETCH_MODELS:\s*'\/api\/v1\/llm-config\/fetch-models'/,
  'LLM config should expose a dynamic model discovery endpoint'
);

assert.doesNotMatch(
  constantsSource,
  /LLM_CONFIG:\s*{[\s\S]*?MODELS:\s*\(provider:\s*string\)[\s\S]*?}\s*,/,
  'LLM config should not expose the legacy preset-model endpoint'
);

assert.match(
  constantsSource,
  /EMBEDDING_CONFIG:\s*{[\s\S]*LIST:\s*'\/api\/v1\/embedding-config\/'/,
  'Embedding config list endpoint should include a trailing slash to avoid FastAPI redirects'
);

assert.match(
  constantsSource,
  /EMBEDDING_CONFIG:\s*{[\s\S]*CREATE:\s*'\/api\/v1\/embedding-config\/'/,
  'Embedding config create endpoint should include a trailing slash to match the backend route'
);

assert.match(
  constantsSource,
  /EMBEDDING_CONFIG:\s*{[\s\S]*FETCH_MODELS:\s*'\/api\/v1\/embedding-config\/fetch-models'/,
  'Embedding config should expose a dynamic model discovery endpoint'
);

assert.doesNotMatch(
  constantsSource,
  /EMBEDDING_CONFIG:\s*{[\s\S]*?MODELS:\s*\(provider:\s*string\)[\s\S]*?}\s*,/,
  'Embedding config should not expose the legacy preset-model endpoint'
);

console.log('settingsApiEndpoints.test.ts passed');
