import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const protectedRouteSource = readFileSync(
  resolve('src/components/common/ProtectedRoute.tsx'),
  'utf8'
);
const useAuthSource = readFileSync(resolve('src/hooks/useAuth.ts'), 'utf8');
const slidegenSource = readFileSync(resolve('src/api/endpoints/slidegen.ts'), 'utf8');
const errorBoundarySource = readFileSync(
  resolve('src/components/common/ErrorBoundary.tsx'),
  'utf8'
);

assert.equal(
  protectedRouteSource.includes('const { user, isCheckingAuth } = useAuth();'),
  true,
  'ProtectedRoute should trigger auth validation and read the current user'
);
assert.equal(
  protectedRouteSource.includes('if (isCheckingAuth) {'),
  true,
  'ProtectedRoute should hold rendering while token validation is in flight'
);
assert.equal(
  protectedRouteSource.includes('if (!isAuthenticated || !user) {'),
  true,
  'ProtectedRoute should reject persisted-but-unverified auth state'
);

assert.equal(
  useAuthSource.includes('setAuthState(token, user);'),
  false,
  'useAuth should not write the token twice after login succeeds'
);
assert.equal(
  useAuthSource.includes('setUser(user);'),
  true,
  'useAuth should update the user profile without duplicating the token write'
);

assert.equal(
  slidegenSource.includes('storage.getToken()'),
  false,
  'slidegen SSE requests should not bypass the auth store with raw localStorage reads'
);
assert.equal(
  slidegenSource.includes('useAuthStore.getState().token'),
  true,
  'slidegen SSE requests should read the latest token from the auth store'
);

assert.equal(
  errorBoundarySource.includes('import.meta.env.DEV'),
  true,
  'ErrorBoundary should only expose stack details in development'
);

console.log('authReviewRegressionsSource.test.ts passed');
