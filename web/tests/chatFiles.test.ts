import assert from 'node:assert/strict';
import { getCurrentFileIds } from '../src/components/chat/chatFiles.ts';

assert.deepEqual(getCurrentFileIds(undefined), []);
assert.deepEqual(getCurrentFileIds({}), []);
assert.deepEqual(getCurrentFileIds({ data: null }), []);
assert.deepEqual(getCurrentFileIds({ data: [{ id: 'file-1' }, { id: 'file-2' }] }), [
  'file-1',
  'file-2',
]);

console.log('chatFiles.test.ts passed');
