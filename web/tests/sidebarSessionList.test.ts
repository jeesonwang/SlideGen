import assert from 'node:assert/strict';
import type { SessionPublic } from '../src/api/types/session.types.ts';
import {
  isSidebarSessionPinned,
  sortSidebarSessions,
  togglePinnedExtraData,
} from '../src/components/common/sidebarSessionList.ts';

const buildSession = (
  id: string,
  update_time: string,
  pinned = false
): SessionPublic => ({
  id,
  user_id: 'user-1',
  title: `Session ${id}`,
  status: 'active',
  topic: null,
  extra_data: pinned ? { pinned: true } : null,
  file_count: 0,
  message_count: 0,
  create_time: '2026-03-17T00:00:00Z',
  update_time,
});

const sessions = [
  buildSession('recent-unpinned', '2026-03-17T10:00:00Z', false),
  buildSession('old-pinned', '2026-03-17T08:00:00Z', true),
  buildSession('recent-pinned', '2026-03-17T09:00:00Z', true),
  buildSession('old-unpinned', '2026-03-17T07:00:00Z', false),
];

assert.equal(isSidebarSessionPinned(sessions[1]), true);
assert.equal(isSidebarSessionPinned(sessions[0]), false);

assert.deepEqual(
  sortSidebarSessions(sessions).map((session) => session.id),
  ['recent-pinned', 'old-pinned', 'recent-unpinned', 'old-unpinned']
);

assert.deepEqual(togglePinnedExtraData(null, true), { pinned: true });
assert.deepEqual(togglePinnedExtraData({ foo: 'bar' }, true), {
  foo: 'bar',
  pinned: true,
});
assert.deepEqual(togglePinnedExtraData({ foo: 'bar', pinned: true }, false), {
  foo: 'bar',
  pinned: false,
});

console.log('sidebarSessionList.test.ts passed');
