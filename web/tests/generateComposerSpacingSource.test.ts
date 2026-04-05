import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const configSource = readFileSync(resolve('src/components/config/ConfigurationPanel.tsx'), 'utf8');

assert.equal(
  chatSource.includes('border-t border-border/70 pt-3.5'),
  true,
  'Composer settings strip should sit slightly closer to the action row'
);

assert.equal(
  chatSource.includes('rounded-[2rem] border border-border/70 bg-surface-100/80 px-6 py-5.5'),
  true,
  'Prompt ingredients card should reduce bottom whitespace with slightly tighter vertical padding'
);

assert.equal(
  chatSource.includes('{renderComposerCard()}'),
  true,
  'ChatInterface should still render the composer directly beneath the intro cards'
);

assert.equal(
  chatSource.includes('grid items-start gap-5 lg:grid-cols-[1.2fr_0.8fr]'),
  true,
  'Generate hero grid should retain the compact two-column layout'
);

assert.equal(
  chatSource.includes('<div className="mt-2.5">{renderComposerCard()}</div>'),
  true,
  'Generate hero should add a small gap between the intro cards and the composer'
);

assert.equal(
  configSource.includes("const fieldClassName = 'flex min-w-0 items-center gap-2 xl:flex-none'"),
  true,
  'ConfigurationPanel should give field labels a touch more breathing room'
);

assert.equal(
  configSource.includes('gap-2.5 rounded-2xl border border-border/70 bg-surface-50 px-3 xl:w-[12.75rem] xl:flex-none'),
  true,
  'ConfigurationPanel should keep enough room and padding for the Web research label and switch'
);

console.log('generateComposerSpacingSource.test.ts passed');
