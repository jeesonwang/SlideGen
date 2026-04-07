import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');

assert.equal(
  chatSource.includes("grid items-start gap-5 lg:grid-cols-[1.2fr_0.8fr]"),
  false,
  'Generate empty state should no longer render the two intro cards grid'
);

assert.equal(
  chatSource.includes("rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-6 shadow-soft"),
  false,
  'Generate empty state should remove the old primary intro card'
);

assert.equal(
  chatSource.includes("mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-surface text-brand-strong"),
  false,
  'Generate empty state should remove the old intro icon card'
);

assert.equal(
  chatSource.includes('Build a presentation brief that is clear enough to generate from'),
  false,
  'Generate empty state should remove the old large intro heading'
);

assert.equal(
  chatSource.includes("rounded-[2rem] border border-border/70 bg-surface-100/80 px-6 py-5.5"),
  false,
  'Generate empty state should remove the old helper card'
);

assert.equal(
  chatSource.includes('Project brief'),
  false,
  'Generate empty state should remove the old helper copy block'
);

console.log('generateHeroCompactLayoutSource.test.ts passed');
