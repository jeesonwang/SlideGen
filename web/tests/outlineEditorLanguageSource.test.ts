import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const outlineEditorSource = readFileSync(
  resolve('src/components/generation/OutlineEditor.tsx'),
  'utf8'
);
const chatSource = readFileSync(
  resolve('src/components/chat/ChatInterface.tsx'),
  'utf8'
);

assert.doesNotMatch(
  outlineEditorSource,
  /[\u4e00-\u9fff]/,
  'OutlineEditor source should use English-only UI copy'
);

assert.doesNotMatch(
  chatSource,
  /[\u4e00-\u9fff]/,
  'ChatInterface source should use English-only UI copy'
);

console.log('outlineEditorLanguageSource.test.ts passed');
