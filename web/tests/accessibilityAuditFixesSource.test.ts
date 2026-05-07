import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const outlineEditorSource = readFileSync(
  resolve('src/components/generation/OutlineEditor.tsx'),
  'utf8'
);
const chatInterfaceSource = readFileSync(
  resolve('src/components/chat/ChatInterface.tsx'),
  'utf8'
);
const composerSource = readFileSync(resolve('src/components/chat/ComposerCard.tsx'), 'utf8');
const chatMessageSource = readFileSync(resolve('src/components/chat/ChatMessageItem.tsx'), 'utf8');

assert.match(
  outlineEditorSource,
  /role="button"[\s\S]*tabIndex=\{0\}[\s\S]*aria-pressed=\{isActive\}/,
  'OutlineEditor should expose the active section container with keyboard-accessible button semantics'
);

for (const label of [
  'Copy message',
  'Edit message',
  'Upload reference files',
  'Send prompt',
]) {
  assert.equal(
    [chatInterfaceSource, composerSource, chatMessageSource].some((source) =>
      source.includes(`aria-label="${label}"`)
    ),
    true,
    `ChatInterface should expose an accessible label for "${label}"`
  );
}

assert.match(
  composerSource,
  /aria-label=\{`Remove reference \$\{file\.filename\}`\}/,
  'ChatInterface should expose an accessible label for removing uploaded files'
);

console.log('accessibilityAuditFixesSource.test.ts passed');
