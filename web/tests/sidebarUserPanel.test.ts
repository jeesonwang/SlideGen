import assert from 'node:assert/strict';
import { getSidebarUserPanelData } from '../src/components/common/sidebarUserPanel.ts';

assert.deepEqual(
  getSidebarUserPanelData({
    username: 'wangjs',
    email: 'wangjs@xisofttec.com',
  }),
  {
    displayName: 'wangjs',
    email: 'wangjs@xisofttec.com',
    initials: 'W',
  }
);

assert.deepEqual(
  getSidebarUserPanelData({
    email: 'demo.user@example.com',
  }),
  {
    displayName: 'demo.user',
    email: 'demo.user@example.com',
    initials: 'D',
  }
);

assert.deepEqual(getSidebarUserPanelData(), {
  displayName: 'User',
  email: '',
  initials: 'U',
});

console.log('sidebarUserPanel.test.ts passed');
