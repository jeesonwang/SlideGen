import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(
  resolve('web/src/components/generation/OutlineEditor.tsx'),
  'utf8'
);
const globalStyles = readFileSync(resolve('web/src/index.css'), 'utf8');

assert.match(
  source,
  /useState<'outline'\s*\|\s*'markdown'>\('outline'\)/,
  'OutlineEditor should track outline/markdown tab state'
);

assert.match(
  source,
  /interface OutlineEditorProps[\s\S]*onRefresh\?:\s*\(\)\s*=>\s*(?:void|Promise<void>)/,
  'OutlineEditor should support an injected refresh callback'
);

assert.doesNotMatch(
  source,
  />\s*Mindmap\s*</,
  'OutlineEditor should no longer show a Mindmap button'
);

assert.match(
  source,
  />\s*Full Screen\s*</,
  'OutlineEditor should expose a Full Screen toolbar action'
);

assert.match(
  source,
  />\s*Download\s*</,
  'OutlineEditor should expose a Download toolbar action'
);

assert.match(
  source,
  />\s*Refresh\s*</,
  'OutlineEditor should expose a Refresh toolbar action'
);

assert.match(
  source,
  /requestFullscreen/,
  'OutlineEditor should include fullscreen support'
);

assert.match(
  source,
  /isFullscreen &&[\s\S]*flex[\s\S]*h-full[\s\S]*flex-col/,
  'OutlineEditor should expand its shell layout when browser fullscreen is active'
);

assert.match(
  source,
  /Blob\(/,
  'OutlineEditor should build a Blob for markdown download'
);

assert.match(
  source,
  /title="Add row"/,
  'OutlineEditor row action should add a blank row instead of duplicating content'
);

assert.doesNotMatch(
  source,
  /title="Duplicate row"/,
  'OutlineEditor should no longer expose a duplicate row action'
);

assert.match(
  source,
  /text-\[13px\]|text-xs/,
  'OutlineEditor should use more compact typography in the workbench'
);

assert.match(
  source,
  /activeView === 'markdown'/,
  'OutlineEditor should still render a markdown view when the Markdown tab is active'
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

assert.match(
  globalStyles,
  /\.outline-editor-shell:fullscreen::backdrop/,
  'Global styles should provide a non-default backdrop for outline fullscreen mode'
);

console.log('outlineEditorSource.test.ts passed');
