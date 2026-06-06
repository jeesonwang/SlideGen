import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const chatInterfaceSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const composerSource = readFileSync(resolve('src/components/chat/ComposerCard.tsx'), 'utf8');

assert.equal(
  composerSource.includes('type="file"'),
  true,
  'ChatInterface should include a hidden file input for inline reference uploads'
);
assert.equal(
  chatInterfaceSource.includes('uploadFileMutation'),
  true,
  'ChatInterface should upload reference files directly from the composer'
);
assert.equal(
  composerSource.includes('selectedReferenceFiles'),
  true,
  'ChatInterface should render an inline list of selected reference files'
);
assert.equal(
  composerSource.includes('Upload references'),
  true,
  'Composer upload action should use presentation-oriented reference copy'
);
assert.equal(
  composerSource.includes('Linked references appear here and are automatically used during generation.'),
  false,
  'Composer should not render redundant empty-state reference helper copy'
);

assert.equal(
  composerSource.includes('workbench-stage-panel'),
  true,
  'ChatInterface should render the composer as a card inside the chat flow'
);

assert.equal(
  composerSource.includes('Tip: shape the structure first, then refine the slides'),
  false,
  'Composer should not render the explanatory tip panel above the prompt input'
);

assert.equal(
  composerSource.includes('Regenerate outline'),
  false,
  'Composer should remove the secondary regenerate outline action from the prompt toolbar'
);

assert.equal(
  chatInterfaceSource.includes('border-b border-border/70 bg-surface-50/95 px-4 pb-6 pt-5 sm:px-6 lg:px-8'),
  false,
  'ChatInterface should not keep the composer attached to the top page shell'
);

const composerIndex = chatInterfaceSource.lastIndexOf('{renderComposerCard()}');

assert.equal(
  chatInterfaceSource.includes('Build a presentation brief that is clear enough to generate from'),
  false,
  'ChatInterface should remove the empty-state intro headline above the composer'
);

assert.equal(
  composerIndex >= 0,
  true,
  'ChatInterface should still render the composer card in the empty state'
);

console.log('composerAttachmentSource.test.ts passed');
