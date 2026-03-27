import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(
  resolve('web/src/components/generation/OutlineEditor.tsx'),
  'utf8'
);

assert.match(
  source,
  /useState<'outline'\s*\|\s*'markdown'>\('outline'\)/,
  'OutlineEditor should track outline/markdown tab state'
);

assert.match(
  source,
  />\s*Markdown\s*</,
  'OutlineEditor should expose a Markdown toggle button'
);

assert.doesNotMatch(
  source,
  />\s*Mindmap\s*</,
  'OutlineEditor should no longer show a Mindmap button'
);

assert.match(
  source,
  /activeView === 'markdown'/,
  'OutlineEditor should render a markdown view when the Markdown tab is active'
);

assert.match(
  source,
  /activeView === 'outline' &&/,
  'OutlineEditor should only show outline-specific title controls in outline view'
);

assert.doesNotMatch(
  source,
  /<Input\.TextArea/,
  'OutlineEditor markdown view should not use a nested TextArea with its own vertical scrolling'
);

assert.doesNotMatch(
  source,
  /text-slate-100/,
  'OutlineEditor markdown preview should not use low-contrast light text'
);

assert.match(
  source,
  /text-text-main/,
  'OutlineEditor markdown preview should use theme-aware readable text'
);

assert.match(
  source,
  /bg-surface-50/,
  'OutlineEditor markdown preview should use a theme-aware background'
);

console.log('outlineEditorSource.test.ts passed');
