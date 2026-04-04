import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatInterfaceSource = readFileSync(
  resolve('src/components/chat/ChatInterface.tsx'),
  'utf8'
);
const generationWizardSource = readFileSync(
  resolve('src/components/generation/GenerationWizard.tsx'),
  'utf8'
);

assert.equal(
  chatInterfaceSource.includes('px-4 py-6 sm:px-6 lg:px-8'),
  true,
  'ChatInterface should use adaptive horizontal padding for narrow and wide screens'
);

assert.equal(
  chatInterfaceSource.includes('mb-8 flex flex-col gap-4 rounded-[2rem] border border-border/70 bg-background px-4 py-4 shadow-soft sm:px-5'),
  true,
  'ChatInterface should keep the inline composer card responsive inside the chat flow'
);

assert.equal(
  chatInterfaceSource.includes('sm:h-7 sm:w-7'),
  false,
  'ChatInterface should keep secondary action hit areas above compact 28px targets'
);

assert.equal(
  generationWizardSource.includes('-mx-3 px-3 sm:-mx-4 sm:px-4 lg:px-8'),
  true,
  'GenerationWizard sticky action bar should adapt its negative margins and padding by breakpoint'
);

console.log('chatResponsiveAuditFixesSource.test.ts passed');
