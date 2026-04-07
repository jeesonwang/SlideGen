import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');

assert.match(
  source,
  /msg\.role === 'user' \? 'items-end group\/user' : ''/,
  'User message content column should align actions to the right beneath the bubble'
);

assert.match(
  source,
  /aria-label="Copy message"[\s\S]*className="flex h-7 w-7 items-center justify-center/,
  'Copy action should use a very compact icon button size beneath user bubbles'
);

assert.match(
  source,
  /aria-label="Edit message"[\s\S]*className="flex h-7 w-7 items-center justify-center/,
  'Edit action should use a very compact icon button size beneath user bubbles'
);

assert.match(
  source,
  /opacity-0 pointer-events-none[\s\S]*group-hover\/user:opacity-100[\s\S]*group-hover\/user:pointer-events-auto/,
  'User message actions should stay hidden until the user bubble is hovered'
);

console.log('chatUserBubbleActionsSource.test.ts passed');
