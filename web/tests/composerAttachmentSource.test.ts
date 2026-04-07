import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');

assert.equal(
  source.includes('type="file"'),
  true,
  'ChatInterface should include a hidden file input for inline reference uploads'
);
assert.equal(
  source.includes('uploadFileMutation'),
  true,
  'ChatInterface should upload reference files directly from the composer'
);
assert.equal(
  source.includes('selectedReferenceFiles'),
  true,
  'ChatInterface should render an inline list of selected reference files'
);
assert.equal(
  source.includes('Upload references'),
  true,
  'Composer upload action should use presentation-oriented reference copy'
);

assert.equal(
  source.includes('mb-8 flex flex-col gap-4 rounded-[2rem] border border-border/70 bg-background px-4 py-4 shadow-soft sm:px-5'),
  true,
  'ChatInterface should render the composer as a card inside the chat flow'
);

assert.equal(
  source.includes('border-b border-border/70 bg-surface-50/95 px-4 pb-6 pt-5 sm:px-6 lg:px-8'),
  false,
  'ChatInterface should not keep the composer attached to the top page shell'
);

const composerIndex = source.lastIndexOf('{renderComposerCard()}');

assert.equal(
  source.includes('Build a presentation brief that is clear enough to generate from'),
  false,
  'ChatInterface should remove the empty-state intro headline above the composer'
);

assert.equal(
  composerIndex >= 0,
  true,
  'ChatInterface should still render the composer card in the empty state'
);

console.log('composerAttachmentSource.test.ts passed');
