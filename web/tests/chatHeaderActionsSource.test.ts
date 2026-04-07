import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');

assert.equal(
  source.includes('New project'),
  false,
  'ChatInterface should not render a redundant New project button in the header'
);

assert.equal(
  source.includes('handleReset'),
  false,
  'ChatInterface should remove the unused reset handler after dropping the header action'
);

console.log('chatHeaderActionsSource.test.ts passed');
