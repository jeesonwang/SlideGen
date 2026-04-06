import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatStoreSource = readFileSync(resolve('src/store/chatStore.ts'), 'utf8');

assert.equal(
  chatStoreSource.includes('msg.content === content'),
  false,
  'chatStore should not match optimistic messages by content'
);
assert.equal(
  chatStoreSource.includes('tempMessageId'),
  true,
  'chatStore should track an explicit temporary message id while reconciling sends'
);
assert.equal(
  chatStoreSource.includes('currentSessionId: get().currentSessionId'),
  false,
  'resetChat should clear the active session id instead of preserving stale references'
);

console.log('chatStoreReviewRegressionsSource.test.ts passed');
