import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const apiClientSource = readFileSync(resolve('src/api/client.ts'), 'utf8');

assert.equal(
  apiClientSource.includes("window.location.replace('/login');"),
  true,
  'apiClient should force navigation back to /login after a 401 on non-login routes'
);
assert.equal(
  apiClientSource.includes("if (!window.location.pathname.includes('/login')) {"),
  true,
  'apiClient should avoid redirect loops when the user is already on the login page'
);
assert.equal(
  apiClientSource.includes("// window.location.href = '/login';"),
  false,
  'apiClient should not leave the 401 redirect commented out'
);

console.log('apiClient401RedirectSource.test.ts passed');
