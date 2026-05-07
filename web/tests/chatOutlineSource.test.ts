import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatInterfaceSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const messageItemSource = readFileSync(resolve('src/components/chat/ChatMessageItem.tsx'), 'utf8');
const chatLogicSource = readFileSync(resolve('src/components/chat/chatLogic.ts'), 'utf8');

assert.match(
  chatInterfaceSource,
  /ChatMessageItem/,
  'ChatInterface should delegate assistant and user message rendering to ChatMessageItem'
);

assert.match(
  chatInterfaceSource,
  /useCreateSession/,
  'ChatInterface should create projects through the React Query session mutation'
);

assert.doesNotMatch(
  chatInterfaceSource,
  /sessionsApi\.create/,
  'ChatInterface should not bypass React Query cache invalidation for project creation'
);

assert.match(
  chatInterfaceSource,
  /usePresentationStream/,
  'ChatInterface should delegate SSE stream handling to a focused hook'
);

assert.match(
  messageItemSource,
  /OutlineEditor/,
  'ChatMessageItem should import and render OutlineEditor for assistant markdown content'
);

assert.match(
  messageItemSource,
  /isPresentationOutlineMarkdown/,
  'ChatMessageItem should use structured outline detection before rendering OutlineEditor'
);

assert.match(
  chatLogicSource,
  /markdownParser\.parse/,
  'Outline detection should parse Markdown instead of relying on raw heading regexes'
);

assert.doesNotMatch(
  chatLogicSource,
  /\^#\\s\+\/m[\s\S]*\^##\\s\+\/m/,
  'Outline detection should not rely on the old paired heading regex'
);

assert.match(
  chatInterfaceSource,
  /onRefreshOutline=\{handleGenerate\}/,
  'ChatInterface should pass ChatMessageItem a refresh callback that reuses handleGenerate'
);

assert.match(
  messageItemSource,
  /onRefresh=\{onRefreshOutline\}/,
  'ChatMessageItem should pass the refresh callback through to OutlineEditor'
);

assert.equal(
  messageItemSource.includes('w-full max-w-[min(100%,78rem)]'),
  true,
  'ChatInterface should give outline assistant rows a full-width container'
);

assert.equal(
  messageItemSource.includes('w-full max-w-[min(100%,72rem)] flex-1'),
  true,
  'ChatInterface should give outline assistant bubbles a full-width content area'
);

assert.match(
  chatInterfaceSource,
  /activeGenerationRef\s*=\s*useRef<HTMLDivElement>\(null\)/,
  'ChatInterface should track a dedicated generation scroll target'
);

assert.match(
  chatInterfaceSource,
  /scrollIntoView\(\{\s*behavior:\s*'smooth',\s*block:\s*'start'\s*\}\)/,
  'ChatInterface should smoothly scroll to the active generation bubble'
);

assert.match(
  chatInterfaceSource,
  /ref=\{activeGenerationRef\}/,
  'ChatInterface should attach the generation scroll target to the active assistant region'
);

console.log('chatOutlineSource.test.ts passed');
