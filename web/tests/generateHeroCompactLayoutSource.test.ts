import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');

assert.equal(
  chatSource.includes("grid items-start gap-5 lg:grid-cols-[1.2fr_0.8fr]"),
  true,
  'Generate hero should tighten the gap between the intro cards without stretching the helper card'
);

assert.equal(
  chatSource.includes("rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-6 shadow-soft"),
  true,
  'Primary generate hero card should use a more compact vertical padding'
);

assert.equal(
  chatSource.includes("mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-surface text-brand-strong"),
  true,
  'Primary generate hero card should reduce the icon block size to save height'
);

assert.equal(
  chatSource.includes("mt-3 max-w-2xl text-[0.95rem] leading-6 text-text-secondary"),
  true,
  'Primary generate hero copy should use tighter spacing and line height'
);

assert.equal(
  chatSource.includes("rounded-[2rem] border border-border/70 bg-surface-100/80 px-6 py-5.5"),
  true,
  'Prompt ingredients card should match the compact vertical rhythm'
);

assert.equal(
  chatSource.includes("mt-3 space-y-2.5 text-sm leading-6 text-text-secondary"),
  true,
  'Prompt ingredients list should reduce spacing to keep more controls above the fold'
);

console.log('generateHeroCompactLayoutSource.test.ts passed');
