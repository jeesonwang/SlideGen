import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const slidegenSource = readFileSync(resolve('src/api/endpoints/slidegen.ts'), 'utf8');
const sseHookSource = readFileSync(resolve('src/hooks/useSSE.ts'), 'utf8');

assert.equal(slidegenSource.includes('getMarkdownStreamRequest'), true);
assert.equal(slidegenSource.includes("method: 'POST'"), true);
assert.equal(slidegenSource.includes("'Content-Type': 'application/json'"), true);
assert.equal(slidegenSource.includes('Authorization: `Bearer ${token}`'), true);
assert.equal(slidegenSource.includes('url.searchParams.append'), false);
assert.equal(sseHookSource.includes('await fetch(target.url'), true);
assert.equal(sseHookSource.includes('new EventSource'), false);

console.log('slidegenStreamRequest.test.ts passed');
