import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(
  resolve('src/components/generation/OutlineEditor.tsx'),
  'utf8'
);
const globalStyles = readFileSync(resolve('src/index.css'), 'utf8');

assert.match(
  source,
  /useState<'outline'\s*\|\s*'markdown'>\('outline'\)/,
  'OutlineEditor should track outline/markdown tab state'
);

assert.match(
  source,
  /interface OutlineEditorProps[\s\S]*onRefresh\?:\s*\(\)\s*=>\s*(?:void|Promise<void>)/,
  'OutlineEditor should support an injected refresh callback'
);

assert.doesNotMatch(
  source,
  />\s*Mindmap\s*</,
  'OutlineEditor should no longer show a Mindmap button'
);

assert.match(
  source,
  />\s*Full Screen\s*</,
  'OutlineEditor should expose a Full Screen toolbar action'
);

assert.match(
  source,
  />\s*Download\s*</,
  'OutlineEditor should expose a Download toolbar action'
);

assert.match(
  source,
  />\s*Refresh\s*</,
  'OutlineEditor should expose a Refresh toolbar action'
);

assert.match(
  source,
  /requestFullscreen/,
  'OutlineEditor should include fullscreen support'
);

assert.match(
  source,
  /isFullscreen &&[\s\S]*flex[\s\S]*h-full[\s\S]*flex-col/,
  'OutlineEditor should expand its shell layout when browser fullscreen is active'
);

assert.match(
  source,
  /Blob\(/,
  'OutlineEditor should build a Blob for markdown download'
);

assert.doesNotMatch(
  source,
  /const (?:iconButtonClassName|compactIconButtonClassName)\s*=/,
  'OutlineEditor should not rely on duplicated bare className constants for action icon buttons'
);

assert.match(
  source,
  /import \{ ActionIconButton \} from '..\/common\/ActionIconButton'/,
  'OutlineEditor should use the shared action icon button component'
);

assert.match(
  source,
  /outline\.chapters\.map/,
  'OutlineEditor should render chapter-aware outlines'
);

assert.doesNotMatch(
  source,
  /outline\.sections/,
  'OutlineEditor should not read the old flat outline.sections shape'
);

assert.match(
  source,
  /title="Add body below"/,
  'OutlineEditor body action should add a blank body row instead of duplicating content'
);

assert.match(
  source,
  /title="Add topic"[\s\S]*handleInsertTopicAfter/,
  'OutlineEditor topic row plus action should add a topic below the current topic'
);

assert.doesNotMatch(
  source,
  /title="Add body"[\s\S]*handleAddBodyToTopic/,
  'OutlineEditor topic row should not expose a direct Add body action'
);

assert.doesNotMatch(
  source,
  /Add topic after/,
  'OutlineEditor should not keep the redundant Add topic after button'
);

assert.doesNotMatch(
  source,
  /Add topic to \$\{section\.title\}/,
  'OutlineEditor section header should not expose the low-value Add topic button'
);

assert.doesNotMatch(
  source,
  /Duplicate section|Duplicate \$\{section\.title\}|CopyOutlined/,
  'OutlineEditor section header should not expose duplicate controls'
);

assert.doesNotMatch(
  source,
  />\s*Add Section Below\s*</,
  'OutlineEditor should not render a separate Add Section Below row between sections'
);

assert.doesNotMatch(
  source,
  />\s*Add Topic\s*<[\s\S]*>\s*Add Body\s*</,
  'OutlineEditor should not render low-value section footer Add Topic/Add Body controls'
);

assert.doesNotMatch(
  source,
  /handleAddItem|smallActionClassName/,
  'OutlineEditor should remove the unused section footer append-item handler and styles'
);

assert.match(
  source,
  /title="Add section below"[\s\S]*handleAddSection\(chapter\.id, index\)/,
  'OutlineEditor should keep section insertion scoped to the current chapter'
);

assert.doesNotMatch(
  source,
  /title="Duplicate row"/,
  'OutlineEditor should no longer expose a duplicate row action'
);

assert.match(
  source,
  /text-\[13px\]|text-xs/,
  'OutlineEditor should use more compact typography in the workbench'
);

assert.match(
  source,
  /const groupSectionItems =/,
  'OutlineEditor should group topic headings with their body rows for compact outline editing'
);

assert.match(
  source,
  /const \[expandedTopicIds, setExpandedTopicIds\]/,
  'OutlineEditor should hide body rows until a topic is expanded'
);

assert.match(
  source,
  /aria-expanded=\{isTopicExpanded\}/,
  'OutlineEditor topic disclosure should expose its expanded state'
);

assert.match(
  source,
  /draggable[\s\S]*handleTopicDragStart/,
  'OutlineEditor should allow topic groups to be reordered by dragging'
);

assert.match(
  source,
  /const moveTopicGroup =/,
  'OutlineEditor should reorder a topic together with its body rows'
);

assert.match(
  source,
  /const moveSection =/,
  'OutlineEditor should allow sections to be reordered by dragging'
);

assert.match(
  source,
  /handleSectionDragStart/,
  'OutlineEditor should expose a dedicated section drag handle'
);

assert.match(
  source,
  /const setOutlineDragImage =[\s\S]*event\.dataTransfer\.setDragImage/,
  'OutlineEditor should use an explicit drag image helper for full outline blocks'
);

assert.match(
  source,
  /handleSectionDragStart[\s\S]*setOutlineDragImage\([^)]*outline-section-drag-preview/,
  'OutlineEditor section drag should preview the whole section block instead of only the drag handle'
);

assert.match(
  source,
  /handleTopicDragStart[\s\S]*setOutlineDragImage\([^)]*outline-topic-drag-preview/,
  'OutlineEditor topic drag should preview the whole topic block instead of only the drag handle'
);

assert.match(
  source,
  /OUTLINE_SECTION_DRAG_TYPE[\s\S]*event\.dataTransfer\.setData\(OUTLINE_SECTION_DRAG_TYPE/,
  'OutlineEditor section drag should store its source id in the native drag payload'
);

assert.match(
  source,
  /event\.dataTransfer\.getData\(OUTLINE_SECTION_DRAG_TYPE\)\s*\|\|\s*draggingSectionId/,
  'OutlineEditor section drop should not rely only on React drag state'
);

assert.doesNotMatch(
  source,
  /dragOverSection\?\.position\s*\?\?\s*'before'/,
  'OutlineEditor section drop should compute the drop position from the current drop event instead of stale drag-over state'
);

assert.match(
  source,
  /OUTLINE_TOPIC_DRAG_TYPE[\s\S]*readTopicDragPayload/,
  'OutlineEditor topic drag should use a typed native payload'
);

assert.match(
  source,
  /hasDragType\(event, OUTLINE_TOPIC_DRAG_TYPE\)[\s\S]*return;[\s\S]*event\.stopPropagation\(\)/,
  'OutlineEditor topic drop should only stop propagation for topic drags'
);

assert.doesNotMatch(
  source,
  /handleItemKindToggle/,
  'OutlineEditor should not let a Topic label click convert the topic into a body row'
);

assert.match(
  source,
  /<span className="w-14 shrink-0 text-left text-\[12px\] font-medium text-text-secondary">\s*Topic\s*<\/span>/,
  'OutlineEditor should render Topic as a non-clickable label'
);

assert.match(
  source,
  /activeView === 'markdown'/,
  'OutlineEditor should still render a markdown view when the Markdown tab is active'
);

assert.match(
  source,
  /activeView === 'outline' &&/,
  'OutlineEditor should only show outline-specific title controls in outline view'
);

assert.match(
  source,
  /max-h-\[(?:78|100)vh\] overflow-y-auto/,
  'OutlineEditor should give the outline assistant bubble a taller scroll area'
);

assert.doesNotMatch(
  source,
  /<Input\.TextArea/,
  'OutlineEditor markdown view should not use a nested TextArea with its own vertical scrolling'
);

assert.doesNotMatch(
  source,
  /text-slate-100/,
  'OutlineEditor markdown preview should not use low-contrast light text'
);

assert.match(
  source,
  /text-text-main/,
  'OutlineEditor markdown preview should use theme-aware readable text'
);

assert.match(
  source,
  /bg-surface-50/,
  'OutlineEditor markdown preview should use a theme-aware background'
);

assert.match(
  globalStyles,
  /\.outline-editor-shell:fullscreen::backdrop/,
  'Global styles should provide a non-default backdrop for outline fullscreen mode'
);

console.log('outlineEditorSource.test.ts passed');
