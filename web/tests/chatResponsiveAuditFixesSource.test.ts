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
  chatInterfaceSource.includes('px-3 sm:px-4 lg:px-8'),
  true,
  'ChatInterface should use adaptive horizontal padding for narrow and wide screens'
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
