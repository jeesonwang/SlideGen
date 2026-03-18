import assert from 'node:assert/strict';
import { shouldRedirectFromLogin } from '../src/pages/auth/loginRedirect.ts';

assert.equal(shouldRedirectFromLogin(false, null), false);
assert.equal(shouldRedirectFromLogin(true, null), false);
assert.equal(
  shouldRedirectFromLogin(true, {
    id: 'user-1',
    email: 'wangjs@xisofttec.com',
    is_active: true,
    is_superuser: true,
    username: 'wangjs',
  }),
  true
);

console.log('loginRedirect.test.ts passed');
