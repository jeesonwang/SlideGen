import assert from 'node:assert/strict';
import { getRightPanelVisibility } from '../src/components/layout/rightPanelVisibility.ts';

assert.deepEqual(getRightPanelVisibility(false), {
  showPanel: true,
  showExpandTrigger: false,
});

assert.deepEqual(getRightPanelVisibility(true), {
  showPanel: false,
  showExpandTrigger: true,
});

console.log('rightPanelVisibility.test.ts passed');
