import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const appSource = readFileSync(resolve('src/App.tsx'), 'utf8');
const chatSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const configSource = readFileSync(resolve('src/components/config/ConfigurationPanel.tsx'), 'utf8');
const sidebarSource = readFileSync(resolve('src/components/common/Sidebar.tsx'), 'utf8');
const outlineSource = readFileSync(resolve('src/components/generation/OutlineEditor.tsx'), 'utf8');
const settingsSource = readFileSync(resolve('src/pages/settings/SettingsPage.tsx'), 'utf8');

assert.match(
  appSource,
  /from '\.\/theme\/tokens'/,
  'App should consume shared theme tokens instead of defining divergent hard-coded values inline'
);

for (const label of [
  'Slide count',
  'Presentation language',
  'Presentation tone',
  'Content density',
  'Web research',
]) {
  assert.equal(
    configSource.includes(`aria-label="${label}"`) || configSource.includes(`aria-label={${JSON.stringify(label)}}`),
    true,
    `ConfigurationPanel should expose an accessible name for "${label}"`
  );
}

assert.equal(
  outlineSource.includes('toolbarActions'),
  true,
  'OutlineEditor should support injecting supplemental toolbar actions for generated outlines'
);

assert.equal(
  chatSource.includes('aria-label="Presentation prompt"'),
  true,
  'ChatInterface should expose an accessible name for the main prompt input'
);
assert.equal(
  chatSource.includes('Start with the topic, audience, and goal, then turn your references into an editable presentation outline.'),
  false,
  'ChatInterface should remove the redundant subtitle beneath the project title'
);
assert.match(
  chatSource,
  /text-\[15px\][\s\S]*sm:text-\[16px\]/,
  'ChatInterface should further reduce the project title size so short titles do not dominate the header'
);
assert.match(
  chatSource,
  /nativeEvent\.isComposing[\s\S]*keyCode === 229/,
  'ChatInterface title renaming should ignore Enter while an IME composition is still active'
);

assert.equal(
  settingsSource.includes('glass-panel'),
  false,
  'SettingsPage should not keep the glass-panel treatment after the audit cleanup'
);

assert.match(
  sidebarSource,
  /group-hover:opacity-100[\s\S]*group-focus-within:opacity-100/,
  'Sidebar overflow actions should remain discoverable for keyboard users'
);
assert.equal(
  sidebarSource.includes('brand-solid-button'),
  true,
  'Sidebar should use the shared solid brand button treatment for its primary action'
);
assert.equal(
  sidebarSource.includes('brand-mark'),
  true,
  'Sidebar should use the shared brand mark treatment for the logo and avatar chips'
);
assert.match(
  sidebarSource,
  /nativeEvent\.isComposing[\s\S]*keyCode === 229/,
  'Sidebar title renaming should ignore Enter while an IME composition is still active'
);
assert.doesNotMatch(
  sidebarSource,
  /handleRenameSubmit\(session\.id,\s*getSessionDisplayTitle\(session\.title,\s*session\.topic\)\)/,
  'Sidebar title renaming should compare against the raw persisted title instead of the derived display title'
);

for (const [name, source] of [['ChatInterface', chatSource]]) {
  assert.equal(
    source.includes('h-10 w-10'),
    false,
    `${name} should avoid 40px square icon buttons for primary interaction targets`
  );
}

assert.equal(
  outlineSource.includes('sm:h-9 sm:w-9'),
  false,
  'OutlineEditor should not shrink toolbar targets below 44px on small screens'
);

console.log('uiAuditRemediationSource.test.ts passed');
