import assert from 'node:assert/strict';
import { SessionStatus, type SessionPublic } from '../src/api/types/session.types.ts';
import {
  getSessionMetaLine,
  getSessionStatusPresentation,
  getSessionSummary,
} from '../src/components/sessions/sessionPresentation.ts';

const session: SessionPublic = {
  id: 'session-1',
  user_id: 'user-1',
  title: 'New Presentation',
  status: SessionStatus.ACTIVE,
  topic: 'Q1 business review',
  extra_data: null,
  file_count: 3,
  message_count: 12,
  create_time: '2026-02-04T12:00:00Z',
  update_time: '2026-02-05T12:00:00Z',
};

assert.equal(getSessionStatusPresentation(SessionStatus.DELETED).label, 'Deleted');
assert.equal(getSessionStatusPresentation(SessionStatus.ACTIVE).color, 'processing');
assert.equal(getSessionMetaLine(session), 'Q1 business review');

const summary = getSessionSummary([
  session,
  { ...session, id: 'session-2', status: SessionStatus.COMPLETED },
]);
assert.equal(summary.total, 2);
assert.equal(summary.active, 1);

console.log('sessionPresentation.test.ts passed');
