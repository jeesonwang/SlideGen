import assert from 'node:assert/strict';
import {
  parseMarkdownToOutline,
  serializeOutlineToMarkdown,
} from '../src/components/generation/outlineModel.ts';

const nestedMarkdown = `# AI Agent

## Foundations
### What is an AI Agent
#### Definition
Autonomous software that can reason and act.
#### Capabilities
Planning, tool use, and memory.

### Where Agents Fit
#### Workflows
Agents coordinate multi-step tasks.`;

const outline = parseMarkdownToOutline(nestedMarkdown);

assert.equal(outline.presentationTitle, 'AI Agent');
assert.equal(outline.chapters.length, 1);
assert.equal(outline.chapters[0]?.title, 'Foundations');
assert.equal(outline.chapters[0]?.sections.length, 2);
assert.equal(outline.chapters[0]?.sections[0]?.title, 'What is an AI Agent');
assert.equal(outline.chapters[0]?.sections[0]?.items.length, 4);
assert.equal(outline.chapters[0]?.sections[0]?.items[0]?.kind, 'heading');
assert.equal(outline.chapters[0]?.sections[0]?.items[0]?.text, 'Definition');
assert.equal(outline.chapters[0]?.sections[0]?.items[1]?.kind, 'bullet');
assert.equal(
  outline.chapters[0]?.sections[0]?.items[1]?.text,
  'Autonomous software that can reason and act.'
);

const serializedNested = serializeOutlineToMarkdown(outline);

assert.equal(
  serializedNested,
  `# AI Agent

## Foundations
### What is an AI Agent
#### Definition
Autonomous software that can reason and act.
#### Capabilities
Planning, tool use, and memory.

### Where Agents Fit
#### Workflows
Agents coordinate multi-step tasks.`
);

const multiParagraphBodyMarkdown = `# AI Agent

## Foundations
### What is an AI Agent
#### Definition
Autonomous software can reason
and act across tools.

It keeps context across steps
and reports progress.`;

const multiParagraphBodyOutline = parseMarkdownToOutline(multiParagraphBodyMarkdown);
const multiParagraphBodyItems =
  multiParagraphBodyOutline.chapters[0]?.sections[0]?.items ?? [];

assert.deepEqual(
  multiParagraphBodyItems.map((item) => item.kind),
  ['heading', 'bullet', 'bullet']
);
assert.equal(
  multiParagraphBodyItems[1]?.text,
  'Autonomous software can reason and act across tools.'
);
assert.equal(
  multiParagraphBodyItems[2]?.text,
  'It keeps context across steps and reports progress.'
);

const serializedMultiBody = serializeOutlineToMarkdown({
  presentationTitle: 'AI Agent',
  chapters: [
    {
      id: 'chapter-1',
      kind: 'chapter',
      title: 'Foundations',
      sections: [
        {
          id: 'section-1',
          kind: 'section',
          title: 'What is an AI Agent',
          items: [
            { id: 'item-1', kind: 'heading', text: 'Definition' },
            { id: 'item-2', kind: 'bullet', text: 'Body paragraph one.' },
            { id: 'item-3', kind: 'bullet', text: 'Body paragraph two.' },
          ],
        },
      ],
    },
  ],
});

assert.equal(
  serializedMultiBody,
  `# AI Agent

## Foundations
### What is an AI Agent
#### Definition
Body paragraph one.

Body paragraph two.`
);
assert.deepEqual(
  parseMarkdownToOutline(serializedMultiBody).chapters[0]?.sections[0]?.items.map(
    (item) => item.text
  ),
  ['Definition', 'Body paragraph one.', 'Body paragraph two.']
);

const legacyMarkdown = `# Storytelling

## Catalog
- Chapter1 The Art and Impact of Storytelling
- Chapter2 Crafting Compelling Narratives

## Chapter 1
### What is Storytelling
Storytelling shapes memory.
### Key Capabilities`;

const legacyOutline = parseMarkdownToOutline(legacyMarkdown);

assert.equal(legacyOutline.chapters.length, 2);
assert.equal(legacyOutline.chapters[0]?.sections[0]?.title, 'Catalog');
assert.equal(legacyOutline.chapters[0]?.sections[0]?.items[0]?.kind, 'bullet');
assert.equal(
  legacyOutline.chapters[0]?.sections[0]?.items[1]?.text,
  'Chapter2 Crafting Compelling Narratives'
);
assert.equal(legacyOutline.chapters[1]?.sections.length, 1);
assert.equal(legacyOutline.chapters[1]?.sections[0]?.title, 'Chapter 1');
assert.deepEqual(
  legacyOutline.chapters[1]?.sections[0]?.items.map((item) => item.kind),
  ['heading', 'bullet', 'heading']
);
assert.equal(
  legacyOutline.chapters[1]?.sections[0]?.items[0]?.text,
  'What is Storytelling'
);

const mixedMarkdown = serializeOutlineToMarkdown({
  presentationTitle: 'Storytelling',
  chapters: [
    {
      id: 'chapter-1',
      kind: 'chapter',
      title: 'Catalog',
      sections: [
        {
          id: 'section-1',
          kind: 'section',
          title: 'Opening',
          items: [
            { id: 'item-1', kind: 'heading', text: 'The Art and Impact of Storytelling' },
            { id: 'item-2', kind: 'bullet', text: 'Crafting Compelling Narratives' },
          ],
        },
      ],
    },
  ],
});

assert.equal(
  mixedMarkdown,
  `# Storytelling

## Catalog
### Opening
#### The Art and Impact of Storytelling
Crafting Compelling Narratives`
);

const reorderBaseMarkdown = `# Drag Test

## First Chapter
### First Section
#### First Topic
First body

## Second Chapter
### Second Section
#### Second Topic
Second body`;

const reorderBaseOutline = parseMarkdownToOutline(reorderBaseMarkdown);
const reorderedOutline = parseMarkdownToOutline(
  `# Drag Test

## Second Chapter
### Second Section
#### Second Topic
Second body

## First Chapter
### First Section
#### First Topic
First body`,
  reorderBaseOutline
);

assert.equal(reorderedOutline.chapters[0]?.id, reorderBaseOutline.chapters[1]?.id);
assert.equal(reorderedOutline.chapters[1]?.id, reorderBaseOutline.chapters[0]?.id);
assert.equal(
  reorderedOutline.chapters[1]?.sections[0]?.items[0]?.id,
  reorderBaseOutline.chapters[0]?.sections[0]?.items[0]?.id
);

const editedOutline = parseMarkdownToOutline(
  `# Drag Test

## First Chapter Updated
### First Section Updated
#### First Topic Updated
First body changed

## Second Chapter
### Second Section
#### Second Topic
Second body`,
  reorderBaseOutline
);

assert.equal(editedOutline.chapters[0]?.id, reorderBaseOutline.chapters[0]?.id);
assert.equal(
  editedOutline.chapters[0]?.sections[0]?.id,
  reorderBaseOutline.chapters[0]?.sections[0]?.id
);
assert.equal(
  editedOutline.chapters[0]?.sections[0]?.items[0]?.id,
  reorderBaseOutline.chapters[0]?.sections[0]?.items[0]?.id
);

console.log('outlineModel.test.ts passed');
