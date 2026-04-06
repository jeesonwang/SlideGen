import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

for (const relativePath of [
  'src/components/common/Layout.tsx',
  'src/components/common/Header.tsx',
  'src/context/LayoutContext.tsx',
  'src/components/layout/rightPanelPolicy.ts',
  'src/components/layout/rightPanelVisibility.ts',
  'src/components/generation/GenerationWizard.tsx',
]) {
  assert.equal(
    existsSync(resolve(relativePath)),
    false,
    `${relativePath} should be removed once the dead-code cleanup is applied`
  );
}

console.log('deadCodeCleanupSource.test.ts passed');
