import assert from 'node:assert/strict';
import { getDefaultRightPanelCollapsed } from '../src/components/layout/rightPanelPolicy.ts';

assert.equal(getDefaultRightPanelCollapsed('/dashboard'), true);
assert.equal(getDefaultRightPanelCollapsed('/generate'), false);
assert.equal(getDefaultRightPanelCollapsed('/settings'), true);

console.log('rightPanelPolicy.test.ts passed');
