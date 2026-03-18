import assert from 'node:assert/strict';
import {
  getSessionsPageContainerClassName,
  getSessionsPageContentClassName,
} from '../src/pages/sessions/sessionsPageLayout.ts';

assert.match(getSessionsPageContainerClassName(), /\boverflow-y-auto\b/);
assert.match(getSessionsPageContainerClassName(), /\bmin-h-0\b/);
assert.match(getSessionsPageContainerClassName(), /\bh-full\b/);
assert.match(getSessionsPageContentClassName(), /\bp-6\b/);
assert.match(getSessionsPageContentClassName(), /\bspace-y-6\b/);

console.log('sessionsPageLayout.test.ts passed');
