import assert from 'node:assert/strict';
import { getDashboardGreetingName } from '../src/pages/dashboard/dashboardDisplay.ts';

assert.equal(getDashboardGreetingName({ username: 'wangjs', email: 'wangjs@xisofttec.com' }), 'wangjs');
assert.equal(
  getDashboardGreetingName({
    username: 'wangjs@xisofttec.com',
    email: 'wangjs@xisofttec.com',
  }),
  'wangjs'
);
assert.equal(getDashboardGreetingName({ email: 'wangjs@xisofttec.com' }), 'wangjs');
assert.equal(getDashboardGreetingName({ email: 'demo.user@example.com' }), 'demo.user');
assert.equal(getDashboardGreetingName({}), 'there');

console.log('dashboardDisplay.test.ts passed');
