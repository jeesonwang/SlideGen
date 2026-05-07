import assert from 'node:assert/strict';
import {
  parseMarkdownToOutline,
  serializeOutlineToMarkdown,
} from '../src/components/generation/outlineModel.ts';

const standardMarkdown = `# AI Agent

## Cover
### The Future of Autonomous Intelligence

## Chapter 1
### What is an AI Agent
### Key Capabilities`;

const outline = parseMarkdownToOutline(standardMarkdown);

assert.equal(outline.presentationTitle, 'AI Agent');
assert.equal(outline.sections.length, 2);
assert.equal(outline.sections[0]?.title, 'Cover');
assert.equal(outline.sections[0]?.items[0]?.kind, 'heading');
assert.equal(
  outline.sections[0]?.items[0]?.text,
  'The Future of Autonomous Intelligence'
);
assert.equal(outline.sections[1]?.items.length, 2);

const bulletMarkdown = `# Storytelling

## Catalog
- Chapter1 The Art and Impact of Storytelling
- Chapter2 Crafting Compelling Narratives`;

const bulletOutline = parseMarkdownToOutline(bulletMarkdown);

assert.equal(bulletOutline.sections.length, 1);
assert.equal(bulletOutline.sections[0]?.items[0]?.kind, 'bullet');
assert.equal(
  bulletOutline.sections[0]?.items[1]?.text,
  'Chapter2 Crafting Compelling Narratives'
);

const mixedMarkdown = serializeOutlineToMarkdown({
  presentationTitle: 'Storytelling',
  sections: [
    {
      id: 'section-1',
      kind: 'section',
      title: 'Catalog',
      items: [
        { id: 'item-1', kind: 'heading', text: 'The Art and Impact of Storytelling' },
        { id: 'item-2', kind: 'bullet', text: 'Crafting Compelling Narratives' },
      ],
    },
  ],
});

assert.equal(
  mixedMarkdown,
  `# Storytelling

## Catalog
### The Art and Impact of Storytelling
- Crafting Compelling Narratives`
);

const tolerantMarkdown = `# Mixed Layout

## Section One

Paragraph that should be kept as a bullet

### Topic Alpha
* Topic Beta`;

const tolerantOutline = parseMarkdownToOutline(tolerantMarkdown);

assert.equal(tolerantOutline.sections.length, 1);
assert.equal(tolerantOutline.sections[0]?.items.length, 3);
assert.deepEqual(
  tolerantOutline.sections[0]?.items.map((item) => item.kind),
  ['bullet', 'heading', 'bullet']
);

const reorderBaseMarkdown = `# Drag Test

## First Section
### First Topic
- First body

## Second Section
### Second Topic
- Second body`;

const reorderBaseOutline = parseMarkdownToOutline(reorderBaseMarkdown);
const reorderedOutline = parseMarkdownToOutline(
  `# Drag Test

## Second Section
### Second Topic
- Second body

## First Section
### First Topic
- First body`,
  reorderBaseOutline
);

assert.equal(reorderedOutline.sections[0]?.id, reorderBaseOutline.sections[1]?.id);
assert.equal(reorderedOutline.sections[1]?.id, reorderBaseOutline.sections[0]?.id);
assert.equal(
  reorderedOutline.sections[1]?.items[0]?.id,
  reorderBaseOutline.sections[0]?.items[0]?.id
);

const editedOutline = parseMarkdownToOutline(
  `# Drag Test

## First Section Updated
### First Topic Updated
- First body changed

## Second Section
### Second Topic
- Second body`,
  reorderBaseOutline
);

assert.equal(editedOutline.sections[0]?.id, reorderBaseOutline.sections[0]?.id);
assert.equal(
  editedOutline.sections[0]?.items[0]?.id,
  reorderBaseOutline.sections[0]?.items[0]?.id
);
assert.equal(
  editedOutline.sections[0]?.items[1]?.id,
  reorderBaseOutline.sections[0]?.items[1]?.id
);

console.log('outlineModel.test.ts passed');
