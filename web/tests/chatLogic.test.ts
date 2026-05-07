import assert from 'node:assert/strict';
import {
  getAssistantMessageContent,
  isPresentationOutlineMarkdown,
  shouldCreateSessionForSend,
} from '../src/components/chat/chatLogic.ts';

const content = getAssistantMessageContent({
  finalContent: '# Final markdown',
  streamingContent: 'partial chunk',
});

assert.equal(content, '# Final markdown');

assert.equal(
  shouldCreateSessionForSend({
    currentSessionId: null,
    hasUser: true,
    content: 'Generate a deck about AI',
  }),
  true
);

assert.equal(
  shouldCreateSessionForSend({
    currentSessionId: null,
    hasUser: true,
    content: '   ',
  }),
  false
);

assert.equal(
  shouldCreateSessionForSend({
    currentSessionId: 'session-1',
    hasUser: true,
    content: 'Generate a deck about AI',
  }),
  false
);

assert.equal(
  isPresentationOutlineMarkdown('# Board Review\n\n## Audience\n\nExecutives'),
  true
);

assert.equal(
  isPresentationOutlineMarkdown('```md\n# Example\n## Nested\n```'),
  false,
  'Markdown heading markers inside code fences should not be treated as outlines'
);

assert.equal(
  isPresentationOutlineMarkdown('Context before the title\n\n# Board Review\n\n## Audience'),
  false,
  'Outline rendering should require the first meaningful Markdown block to be the deck title'
);

console.log('chatLogic.test.ts passed');
