import assert from 'node:assert/strict';
import { getRightPanelVisibility } from '../src/components/layout/rightPanelVisibility.ts';

assert.deepEqual(getRightPanelVisibility(false), {
  showPanel: false,
  showExpandTrigger: false,
});

assert.deepEqual(getRightPanelVisibility(true), {
  showPanel: false,
  showExpandTrigger: false,
});

console.log('rightPanelVisibility.test.ts passed');
