import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const files = [
  'src/components/generation/OutlineEditor.tsx',
  'src/components/generation/MarkdownEditor.tsx',
  'src/components/generation/TopicInput.tsx',
  'src/components/generation/StreamingProgress.tsx',
];

const forbiddenPatterns = [
  'text-gray-',
  'bg-gray-',
  'border-gray-',
  'text-slate-',
  'bg-slate-',
  'border-slate-',
  'bg-white',
];

for (const relativePath of files) {
  const content = readFileSync(resolve(relativePath), 'utf8');

  for (const pattern of forbiddenPatterns) {
    assert.equal(
      content.includes(pattern),
      false,
      `${relativePath} should not contain hard-coded surface/text token: ${pattern}`
    );
  }
}

console.log('generationThemeSource.test.ts passed');
