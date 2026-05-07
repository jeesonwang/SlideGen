import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');

assert.equal(
  source.includes('New project'),
  false,
  'ChatInterface should not render a redundant New project button in the header'
);

assert.equal(
  source.includes('handleReset'),
  false,
  'ChatInterface should remove the unused reset handler after dropping the header action'
);

assert.equal(
  source.includes('currentProjectStatus'),
  false,
  'ChatInterface should not keep a redundant project status label above the session title'
);

assert.equal(
  source.includes('Project ready'),
  false,
  'ChatInterface should not render the redundant Project ready status copy in the header'
);

assert.match(
  source,
  /border-b border-border\/70 bg-surface-50\/88 px-4 py-3/,
  'ChatInterface should use a compact session header'
);

assert.match(
  source,
  /text-\[15px\][\s\S]*sm:text-\[16px\]/,
  'ChatInterface session title should use a smaller product UI font size'
);

console.log('chatHeaderActionsSource.test.ts passed');
