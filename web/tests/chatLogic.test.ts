import assert from 'node:assert/strict';
import {
  getAssistantMessageContent,
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

console.log('chatLogic.test.ts passed');
