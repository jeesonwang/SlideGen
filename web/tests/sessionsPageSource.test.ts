import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const sessionsPageSource = readFileSync(
  resolve('src/pages/sessions/SessionsPage.tsx'),
  'utf8'
);
const sessionListSource = readFileSync(
  resolve('src/components/sessions/SessionList.tsx'),
  'utf8'
);
const useSessionsSource = readFileSync(
  resolve('src/hooks/useSessions.ts'),
  'utf8'
);

assert.equal(sessionsPageSource.includes('useArchiveSession'), false);
assert.equal(sessionsPageSource.includes('archiveMutation'), false);
assert.equal(sessionsPageSource.includes('handleArchive'), false);
assert.equal(sessionsPageSource.includes('Archived {summary.archived}'), false);
assert.equal(sessionsPageSource.includes('review archived work'), false);

assert.equal(sessionListSource.includes('onArchive'), false);
assert.equal(sessionListSource.includes("label: 'Archive'"), false);
assert.equal(sessionListSource.includes("{ text: 'Archived'"), false);
assert.equal(sessionListSource.includes("{ text: 'Deleted'"), false);

assert.equal(useSessionsSource.includes('export const useArchiveSession = () => {'), false);

console.log('sessionsPageSource.test.ts passed');
