import assert from 'node:assert/strict';
import type { SessionPublic, SessionUpdate } from '../src/api/types/session.types.ts';
import { mergeSessionWithUpdate } from '../src/hooks/sessionQueryCache.ts';

const originalSession: SessionPublic = {
  id: 'session-1',
  user_id: 'user-1',
  title: 'Untitled Presentation',
  status: 'active',
  topic: null,
  extra_data: { pinned: false },
  file_count: 0,
  message_count: 0,
  create_time: '2026-04-04T00:00:00Z',
  update_time: '2026-04-04T00:00:00Z',
};

const update: SessionUpdate = {
  title: 'Board Review',
  topic: 'AI agents in operations',
};

assert.deepEqual(mergeSessionWithUpdate(originalSession, update), {
  ...originalSession,
  title: 'Board Review',
  topic: 'AI agents in operations',
});

assert.deepEqual(
  mergeSessionWithUpdate(originalSession, {
    title: undefined,
    topic: null,
  }),
  originalSession
);

console.log('sessionMutationResult.test.ts passed');
