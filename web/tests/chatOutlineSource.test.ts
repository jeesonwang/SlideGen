import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');

assert.match(
  source,
  /OutlineEditor/,
  'ChatInterface should import and render OutlineEditor for assistant markdown content'
);

assert.match(
  source,
  /onRefresh=\{\(\)\s*=>\s*void handleGenerate\(\)\}/,
  'ChatInterface should pass OutlineEditor a refresh callback that reuses handleGenerate'
);

assert.equal(
  source.includes('w-full max-w-[min(100%,78rem)]'),
  true,
  'ChatInterface should give outline assistant rows a full-width container'
);

assert.equal(
  source.includes('w-full max-w-[min(100%,72rem)] flex-1'),
  true,
  'ChatInterface should give outline assistant bubbles a full-width content area'
);

assert.match(
  source,
  /activeGenerationRef\s*=\s*useRef<HTMLDivElement>\(null\)/,
  'ChatInterface should track a dedicated generation scroll target'
);

assert.match(
  source,
  /scrollIntoView\(\{\s*behavior:\s*'smooth',\s*block:\s*'start'\s*\}\)/,
  'ChatInterface should smoothly scroll to the active generation bubble'
);

assert.match(
  source,
  /ref=\{activeGenerationRef\}/,
  'ChatInterface should attach the generation scroll target to the active assistant region'
);

console.log('chatOutlineSource.test.ts passed');
