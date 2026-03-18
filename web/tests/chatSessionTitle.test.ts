import assert from 'node:assert/strict';
import {
  getChatHeaderTitle,
  getUpdatedSessionTitle,
  shouldSubmitTitleChange,
} from '../src/components/chat/chatSessionTitle.ts';

assert.equal(getChatHeaderTitle(), 'AI Presentation Assistant');
assert.equal(getChatHeaderTitle('  Strategy Deck  '), 'Strategy Deck');

assert.equal(getUpdatedSessionTitle('  Board Review  ', 'New Presentation'), 'Board Review');
assert.equal(getUpdatedSessionTitle('   ', 'New Presentation'), 'New Presentation');
assert.equal(getUpdatedSessionTitle('   ', ''), '');

assert.equal(shouldSubmitTitleChange('Roadmap', 'New Presentation'), true);
assert.equal(shouldSubmitTitleChange('  New Presentation  ', 'New Presentation'), false);
assert.equal(shouldSubmitTitleChange('   ', 'New Presentation'), false);
assert.equal(shouldSubmitTitleChange('   ', ''), false);

console.log('chatSessionTitle.test.ts passed');
