import assert from 'node:assert/strict';
import { QueryClient } from '@tanstack/react-query';
import type { SessionPublic, SessionsPublic } from '../src/api/types/session.types.ts';
import { syncUpdatedSessionInCache } from '../src/hooks/sessionQueryCache.ts';

const buildSession = (overrides?: Partial<SessionPublic>): SessionPublic => ({
  id: 'session-1',
  user_id: 'user-1',
  title: 'Untitled Presentation',
  status: 'active',
  topic: null,
  extra_data: null,
  file_count: 0,
  message_count: 0,
  create_time: '2026-04-04T00:00:00Z',
  update_time: '2026-04-04T00:00:00Z',
  ...overrides,
});

const queryClient = new QueryClient();
const originalSession = buildSession();
const untouchedSession = buildSession({
  id: 'session-2',
  title: 'Keep me',
});

queryClient.setQueryData(['sessions', originalSession.id], originalSession);
queryClient.setQueryData(
  ['sessions', { limit: 10, status: 'active' }],
  {
    data: [originalSession, untouchedSession],
    count: 2,
  } satisfies SessionsPublic
);

const updatedSession = buildSession({
  title: 'Board Review',
  topic: 'AI agents for enterprise workflows',
  update_time: '2026-04-04T00:05:00Z',
});

syncUpdatedSessionInCache(queryClient, updatedSession);

const sessionDetail = queryClient.getQueryData<SessionPublic>(['sessions', originalSession.id]);
assert.equal(sessionDetail?.title, 'Board Review');
assert.equal(sessionDetail?.topic, 'AI agents for enterprise workflows');

const sessionsList = queryClient.getQueryData<SessionsPublic>([
  'sessions',
  { limit: 10, status: 'active' },
]);
assert.equal(sessionsList?.data[0]?.title, 'Board Review');
assert.equal(sessionsList?.data[0]?.topic, 'AI agents for enterprise workflows');
assert.equal(sessionsList?.data[1]?.title, 'Keep me');

console.log('sessionQueryCache.test.ts passed');
