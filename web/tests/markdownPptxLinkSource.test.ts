import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const typesSource = readFileSync(resolve('src/api/types/slidegen.types.ts'), 'utf8');
const slidegenSource = readFileSync(resolve('src/api/endpoints/slidegen.ts'), 'utf8');
const constantsSource = readFileSync(resolve('src/utils/constants.ts'), 'utf8');
const chatInterfaceSource = readFileSync(resolve('src/components/chat/ChatInterface.tsx'), 'utf8');
const chatMessageSource = readFileSync(resolve('src/components/chat/ChatMessageItem.tsx'), 'utf8');
const actionBubblePath = resolve('src/components/generation/ActionBubble.tsx');

assert.equal(typesSource.includes('export interface ThemePreset'), true);
assert.match(typesSource, /theme_preset\?: string \| null/);
assert.match(typesSource, /success: boolean[\s\S]*result: \{[\s\S]*output_path: string[\s\S]*filename: string[\s\S]*download_url: string/);
assert.equal(typesSource.includes('task_id: string'), false);

assert.equal(constantsSource.includes("THEME_PRESETS: '/api/v1/slidegen/theme-presets'"), true);
assert.equal(slidegenSource.includes('getThemePresets'), true);
assert.equal(slidegenSource.includes('API_ENDPOINTS.SLIDEGEN.THEME_PRESETS'), true);
assert.equal(slidegenSource.includes('downloadPPTX: async (filename: string)'), true);
assert.equal(slidegenSource.includes('DOWNLOAD(filename)'), true);

assert.equal(existsSync(actionBubblePath), true);
const actionBubbleSource = readFileSync(actionBubblePath, 'utf8');
assert.equal(actionBubbleSource.includes('interface ActionBubbleProps'), true);
assert.equal(actionBubbleSource.includes('markdownContent: string'), true);
assert.equal(actionBubbleSource.includes('slidegenApi.generatePPTXFromMarkdown'), true);
assert.equal(actionBubbleSource.includes('slidegenApi.getThemePresets'), true);
assert.equal(actionBubbleSource.includes('Generate PPTX'), true);
assert.equal(actionBubbleSource.includes('Download PPTX'), true);
assert.equal(actionBubbleSource.includes('Auto Theme'), true);
assert.equal(actionBubbleSource.includes("'auto'"), true);
assert.equal(actionBubbleSource.includes('PPT template'), true);
assert.equal(actionBubbleSource.includes('Choose the slide structure and base layout.'), true);
assert.equal(actionBubbleSource.includes('PPT theme'), true);
assert.equal(
  actionBubbleSource.includes('Automatically match colors, typography, and accents to the content.'),
  true
);
assert.equal(actionBubbleSource.includes('-mt-1'), false);
assert.equal(actionBubbleSource.includes('rounded-[1.75rem] border border-border/70'), true);

assert.equal(chatMessageSource.includes("import { ActionBubble } from '../generation/ActionBubble';"), true);
assert.match(chatMessageSource, /<OutlineEditor[\s\S]*<ActionBubble/);
assert.equal(chatMessageSource.includes("Ready to export"), true);
assert.equal(chatInterfaceSource.includes("flex flex-col gap-0"), false);
assert.equal(chatMessageSource.includes("flex flex-col gap-0"), false);
assert.equal(chatInterfaceSource.includes('toolbarActions='), false);
assert.equal(chatMessageSource.includes('toolbarActions='), false);
assert.equal(chatInterfaceSource.includes('Select theme'), false);
assert.equal(chatMessageSource.includes('Select theme'), false);
assert.equal(chatInterfaceSource.includes('BgColorsOutlined'), false);
assert.equal(chatMessageSource.includes('BgColorsOutlined'), false);

console.log('markdownPptxLinkSource.test.ts passed');
