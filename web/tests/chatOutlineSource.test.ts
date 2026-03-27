import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('web/src/components/chat/ChatInterface.tsx'), 'utf8');

assert.match(
  source,
  /OutlineEditor/,
  'ChatInterface should import and render OutlineEditor for assistant markdown content'
);

assert.match(
  source,
  /msg\.role === 'assistant' && isOutlineMarkdown\(msg\.content\)\s*\?\s*"w-full max-w-\[min\(100%,78rem\)\]"/,
  'ChatInterface should give outline assistant rows a full-width container'
);

assert.match(
  source,
  /msg\.role === 'assistant' && isOutlineMarkdown\(msg\.content\)\s*\?\s*"w-full max-w-\[min\(100%,72rem\)\] flex-1"/,
  'ChatInterface should give outline assistant bubbles a full-width content area'
);

console.log('chatOutlineSource.test.ts passed');
