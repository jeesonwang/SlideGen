import assert from 'node:assert/strict';
import { resolveSectionDropPosition } from '../src/components/generation/outlineDrag.ts';

assert.equal(
  resolveSectionDropPosition({
    sourceIndex: 0,
    targetIndex: 1,
    pointerY: 10,
    targetTop: 0,
    targetHeight: 100,
  }),
  'after',
  'dragging a section downward onto the next section should move it after the target'
);

assert.equal(
  resolveSectionDropPosition({
    sourceIndex: 1,
    targetIndex: 0,
    pointerY: 90,
    targetTop: 0,
    targetHeight: 100,
  }),
  'before',
  'dragging a section upward onto the previous section should move it before the target'
);

assert.equal(
  resolveSectionDropPosition({
    sourceIndex: 0,
    targetIndex: 0,
    pointerY: 90,
    targetTop: 0,
    targetHeight: 100,
  }),
  'after',
  'dropping onto the same section should still use pointer position for visual feedback'
);

assert.equal(
  resolveSectionDropPosition({
    sourceIndex: -1,
    targetIndex: 1,
    pointerY: 90,
    targetTop: 0,
    targetHeight: 100,
  }),
  'after',
  'missing section indexes should fall back to pointer position'
);

console.log('outlineDrag.test.ts passed');
