import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const authStoreSource = readFileSync(resolve('src/store/authStore.ts'), 'utf8');

assert.equal(
  authStoreSource.includes('localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);'),
  false,
  'authStore should not duplicate persisted token writes into a separate raw localStorage key'
);
assert.equal(
  authStoreSource.includes('localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);'),
  false,
  'authStore logout should not depend on clearing a second raw token entry'
);
assert.equal(
  authStoreSource.includes("name: 'auth-storage'"),
  true,
  'authStore should continue to persist auth state via Zustand persist'
);

console.log('authStorePersistenceSource.test.ts passed');
