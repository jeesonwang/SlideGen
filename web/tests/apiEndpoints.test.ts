import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('web/src/utils/constants.ts'), 'utf8');

assert.equal(source.includes("LIST: '/api/v1/sessions/'"), true);
assert.equal(source.includes("CREATE: '/api/v1/sessions/'"), true);
assert.equal(source.includes("LIST: '/api/v1/files/'"), true);

console.log('apiEndpoints.test.ts passed');
