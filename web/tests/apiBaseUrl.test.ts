import assert from 'node:assert/strict';
import { buildApiUrl, resolveApiBaseUrl } from '../src/api/baseUrl.ts';

assert.equal(resolveApiBaseUrl(undefined, true), '');
assert.equal(resolveApiBaseUrl(undefined, false), 'http://127.0.0.1:7860');
assert.equal(resolveApiBaseUrl('http://example.com', true), 'http://example.com');

assert.equal(buildApiUrl('/api/v1/login/access-token', undefined, true), '/api/v1/login/access-token');
assert.equal(
  buildApiUrl('/api/v1/login/access-token', undefined, false),
  'http://127.0.0.1:7860/api/v1/login/access-token'
);
assert.equal(
  buildApiUrl('/api/v1/login/access-token', 'http://example.com', true),
  'http://example.com/api/v1/login/access-token'
);

console.log('apiBaseUrl.test.ts passed');
