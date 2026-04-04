import assert from 'node:assert/strict';
import {
  getChatHeaderTitle,
  getSessionDisplayTitle,
  getUpdatedSessionTitle,
  shouldSubmitTitleChange,
} from '../src/components/chat/chatSessionTitle.ts';

assert.equal(getChatHeaderTitle(), 'Untitled Presentation');
assert.equal(getChatHeaderTitle('  Strategy Deck  '), 'Strategy Deck');
assert.equal(getChatHeaderTitle(' 1 ', 'Autonomous agents overview'), '1');
assert.equal(getChatHeaderTitle('Section 1', 'Autonomous agents overview'), 'Autonomous agents overview');
assert.equal(
  getChatHeaderTitle('Untitled Presentation', null, 'Autonomous agents overview'),
  'Autonomous agents overview'
);

assert.equal(getSessionDisplayTitle(' 1 ', 'Autonomous agents overview'), '1');
assert.equal(getSessionDisplayTitle('123', null), '123');
assert.equal(getSessionDisplayTitle('Section 2', null), 'Untitled Presentation');
assert.equal(getSessionDisplayTitle('  Board Review  ', 'Ignored topic'), 'Board Review');

assert.equal(getUpdatedSessionTitle('  Board Review  ', 'Untitled Presentation'), 'Board Review');
assert.equal(getUpdatedSessionTitle('   ', 'Untitled Presentation'), 'Untitled Presentation');
assert.equal(getUpdatedSessionTitle('   ', ''), '');

assert.equal(shouldSubmitTitleChange('Roadmap', 'Untitled Presentation'), true);
assert.equal(shouldSubmitTitleChange('  Untitled Presentation  ', 'Untitled Presentation'), false);
assert.equal(shouldSubmitTitleChange('   ', 'Untitled Presentation'), false);
assert.equal(shouldSubmitTitleChange('   ', ''), false);

console.log('chatSessionTitle.test.ts passed');
