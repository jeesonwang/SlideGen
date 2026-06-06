import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve('src/components/chat/ChatMessageItem.tsx'), 'utf8');

assert.equal(
  /Cancel[\s\S]*className="[^"]*bg-white/.test(source),
  false,
  'Message edit Cancel button should not force a white background in dark mode'
);

assert.match(
  source,
  /Cancel[\s\S]*className="[^"]*bg-surface-100[^"]*hover:bg-surface-200/,
  'Message edit Cancel button should use theme-aware secondary surface colors'
);

console.log('chatEditActionsThemeSource.test.ts passed');
