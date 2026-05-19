import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Input, Tooltip } from 'antd';
import {
  CaretDownOutlined,
  CaretRightOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FullscreenExitOutlined,
  FullscreenOutlined,
  HolderOutlined,
  OrderedListOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { cn } from '../../utils/classnames';
import { ActionIconButton } from '../common/ActionIconButton';
import type {
  OutlineChapter,
  OutlineCatalogItem,
  OutlineDocument,
  OutlineItem,
  OutlineItemKind,
  OutlineSection,
} from './outlineModel';
import { resolveSectionDropPosition } from './outlineDrag';
import {
  getOutlineCatalogItems,
  parseMarkdownToOutline,
  serializeOutlineToMarkdown,
} from './outlineModel';

const { TextArea } = Input;

const OUTLINE_SECTION_DRAG_TYPE = 'application/x-slidegen-outline-section';
const OUTLINE_TOPIC_DRAG_TYPE = 'application/x-slidegen-outline-topic';

interface OutlineEditorProps {
  value: string;
  onChange: (value: string) => void;
  onRefresh?: () => void | Promise<void>;
  refreshDisabled?: boolean;
  refreshing?: boolean;
  allowFullscreen?: boolean;
  toolbarActions?: React.ReactNode;
}

const EMPTY_OUTLINE: OutlineDocument = {
  presentationTitle: '',
  chapters: [],
};

interface OutlineSectionEntry {
  chapter: OutlineChapter;
  chapterIndex: number;
  section: OutlineSection;
  sectionIndex: number;
}

interface OutlineTopicGroup {
  id: string;
  topic: OutlineItem;
  bodyItems: OutlineItem[];
}

interface GroupedSectionItems {
  looseBodyItems: OutlineItem[];
  topics: OutlineTopicGroup[];
}

const groupSectionItems = (items: OutlineItem[]): GroupedSectionItems => {
  const looseBodyItems: OutlineItem[] = [];
  const topics: OutlineTopicGroup[] = [];
  let currentTopic: OutlineTopicGroup | null = null;

  items.forEach((item) => {
    if (item.kind === 'heading') {
      currentTopic = {
        id: item.id,
        topic: item,
        bodyItems: [],
      };
      topics.push(currentTopic);
      return;
    }

    if (currentTopic) {
      currentTopic.bodyItems.push(item);
      return;
    }

    looseBodyItems.push(item);
  });

  return { looseBodyItems, topics };
};

const flattenGroupedSectionItems = (
  looseBodyItems: OutlineItem[],
  topics: OutlineTopicGroup[]
): OutlineItem[] => [
  ...looseBodyItems,
  ...topics.flatMap((topicGroup) => [topicGroup.topic, ...topicGroup.bodyItems]),
];

const hasDragType = (event: React.DragEvent<HTMLElement>, dragType: string) =>
  Array.from(event.dataTransfer.types).includes(dragType);

const setOutlineDragImage = (
  event: React.DragEvent<HTMLElement>,
  previewSelector: string
) => {
  const previewElement = event.currentTarget.closest<HTMLElement>(previewSelector);
  if (!previewElement) {
    return;
  }

  const previewBounds = previewElement.getBoundingClientRect();
  const offsetX = Math.max(0, Math.min(event.clientX - previewBounds.left, previewBounds.width));
  const offsetY = Math.max(0, Math.min(event.clientY - previewBounds.top, previewBounds.height));

  event.dataTransfer.setDragImage(previewElement, offsetX, offsetY);
};

const readTopicDragPayload = (event: React.DragEvent<HTMLElement>) => {
  const payload = event.dataTransfer.getData(OUTLINE_TOPIC_DRAG_TYPE);
  if (!payload) {
    return null;
  }

  try {
    const parsedPayload = JSON.parse(payload) as Partial<{
      sectionId: string;
      topicId: string;
    }>;

    if (!parsedPayload.sectionId || !parsedPayload.topicId) {
      return null;
    }

    return {
      sectionId: parsedPayload.sectionId,
      topicId: parsedPayload.topicId,
    };
  } catch {
    return null;
  }
};

const createSection = (index: number, localIdToken: string): OutlineSection => ({
  id: `section-local-${localIdToken}-${index}`,
  kind: 'section',
  title: `Section ${index + 1}`,
  items: [
    {
      id: `item-local-${localIdToken}-${index}-0`,
      kind: 'heading',
      text: 'New topic',
    },
  ],
});

const createChapter = (index: number, localIdToken: string): OutlineChapter => ({
  id: `chapter-local-${localIdToken}-${index}`,
  kind: 'chapter',
  title: `Chapter ${index + 1}`,
  sections: [createSection(0, `${localIdToken}-0`)],
});

const createItem = (
  sectionId: string,
  index: number,
  kind: OutlineItemKind,
  localIdToken: string
): OutlineItem => ({
  id: `${sectionId}-${kind}-${localIdToken}-${index}`,
  kind,
  text: kind === 'heading' ? 'New topic' : 'New body point',
});

const toDownloadFilename = (title: string) => {
  const normalized = title
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

  return `${normalized || 'outline'}.md`;
};

export const OutlineEditor: React.FC<OutlineEditorProps> = ({
  value,
  onChange,
  onRefresh,
  refreshDisabled = false,
  refreshing = false,
  allowFullscreen = true,
  toolbarActions,
}) => {
  const [activeView, setActiveView] = useState<'outline' | 'markdown'>('outline');
  const [activeChapterId, setActiveChapterId] = useState<string | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [expandedTopicIds, setExpandedTopicIds] = useState<string[]>([]);
  const [draggingTopic, setDraggingTopic] = useState<{
    sectionId: string;
    topicId: string;
  } | null>(null);
  const [dragOverTopicId, setDragOverTopicId] = useState<string | null>(null);
  const [draggingSectionId, setDraggingSectionId] = useState<string | null>(null);
  const [dragOverSection, setDragOverSection] = useState<{
    sectionId: string;
    position: 'before' | 'after';
  } | null>(null);
  const [isPseudoFullscreen, setIsPseudoFullscreen] = useState(false);
  const [isBrowserFullscreen, setIsBrowserFullscreen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const previousOutlineRef = useRef<OutlineDocument | null>(null);
  const localIdCounterRef = useRef(0);
  const outline = useMemo<OutlineDocument>(
    () => {
      // The editor serializes to Markdown on every change, so the parser needs the
      // previous outline as reconciliation context to preserve drag/drop identities.
      // eslint-disable-next-line react-hooks/refs
      const previousOutline = previousOutlineRef.current;
      return value.trim() ? parseMarkdownToOutline(value, previousOutline) : EMPTY_OUTLINE;
    },
    [value]
  );
  const sectionEntries = useMemo<OutlineSectionEntry[]>(
    () =>
      outline.chapters.flatMap((chapter, chapterIndex) =>
        chapter.sections.map((section, sectionIndex) => ({
          chapter,
          chapterIndex,
          section,
          sectionIndex,
        }))
      ),
    [outline]
  );
  const catalogItems = useMemo<OutlineCatalogItem[]>(
    () => getOutlineCatalogItems(outline),
    [outline]
  );
  const resolvedActiveChapterId =
    activeChapterId && outline.chapters.some((chapter) => chapter.id === activeChapterId)
      ? activeChapterId
      : outline.chapters[0]?.id ?? null;
  const resolvedActiveSectionId =
    activeSectionId && sectionEntries.some((entry) => entry.section.id === activeSectionId)
      ? activeSectionId
      : sectionEntries[0]?.section.id ?? null;
  const currentMarkdown = serializeOutlineToMarkdown(outline);
  const canRefresh = !!onRefresh && !refreshDisabled;
  const isFullscreen = isBrowserFullscreen || isPseudoFullscreen;

  useEffect(() => {
    previousOutlineRef.current = outline;
  }, [outline]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      if (typeof document === 'undefined') {
        return;
      }

      setIsBrowserFullscreen(document.fullscreenElement === rootRef.current);
      if (document.fullscreenElement !== rootRef.current) {
        setIsPseudoFullscreen(false);
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const syncMarkdown = (nextOutline: OutlineDocument) => {
    previousOutlineRef.current = nextOutline;
    onChange(serializeOutlineToMarkdown(nextOutline));
  };

  const nextLocalIdToken = () => {
    localIdCounterRef.current += 1;
    return `${localIdCounterRef.current}`;
  };

  const updateSectionById = (
    sectionId: string,
    updater: (section: OutlineSection) => OutlineSection
  ): OutlineDocument => ({
    ...outline,
    chapters: outline.chapters.map((chapter) => ({
      ...chapter,
      sections: chapter.sections.map((section) =>
        section.id === sectionId ? updater(section) : section
      ),
    })),
  });

  const findSectionEntry = (sectionId: string) =>
    sectionEntries.find((entry) => entry.section.id === sectionId) ?? null;

  const getSectionDropPosition = (
    event: React.DragEvent<HTMLElement>,
    targetSectionId: string
  ) => {
    const sourceSectionId =
      event.dataTransfer.getData(OUTLINE_SECTION_DRAG_TYPE) || draggingSectionId;
    const sourceIndex = sectionEntries.findIndex(
      (entry) => entry.section.id === sourceSectionId
    );
    const targetIndex = sectionEntries.findIndex(
      (entry) => entry.section.id === targetSectionId
    );
    const sectionBounds = event.currentTarget.getBoundingClientRect();

    return resolveSectionDropPosition({
      sourceIndex,
      targetIndex,
      pointerY: event.clientY,
      targetTop: sectionBounds.top,
      targetHeight: sectionBounds.height,
    });
  };

  const handleDownload = () => {
    const blob = new Blob([currentMarkdown || '# Empty outline'], {
      type: 'text/markdown;charset=utf-8',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = toDownloadFilename(outline.presentationTitle);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleFullscreenToggle = async () => {
    if (!allowFullscreen || !rootRef.current) {
      return;
    }

    if (typeof document !== 'undefined' && document.fullscreenElement === rootRef.current) {
      await document.exitFullscreen?.();
      return;
    }

    if (rootRef.current.requestFullscreen) {
      try {
        await rootRef.current.requestFullscreen();
        return;
      } catch {
        setIsPseudoFullscreen((current) => !current);
        return;
      }
    }

    setIsPseudoFullscreen((current) => !current);
  };

  const handlePresentationTitleChange = (nextTitle: string) => {
    syncMarkdown({
      ...outline,
      presentationTitle: nextTitle,
    });
  };

  const handleSectionTitleChange = (sectionId: string, title: string) => {
    syncMarkdown(updateSectionById(sectionId, (section) => ({ ...section, title })));
  };

  const handleItemTextChange = (sectionId: string, itemId: string, text: string) => {
    syncMarkdown(
      updateSectionById(sectionId, (section) => ({
        ...section,
        items: section.items.map((item) =>
          item.id === itemId ? { ...item, text } : item
        ),
      }))
    );
  };

  const handleChapterTitleChange = (chapterId: string, title: string) => {
    syncMarkdown({
      ...outline,
      chapters: outline.chapters.map((chapter) =>
        chapter.id === chapterId ? { ...chapter, title } : chapter
      ),
    });
  };

  const handleCatalogItemTitleChange = (catalogItem: OutlineCatalogItem, title: string) => {
    handleChapterTitleChange(catalogItem.chapterId, title);
  };

  const handleDeleteChapter = (chapterId: string) => {
    syncMarkdown({
      ...outline,
      chapters: outline.chapters.filter((chapter) => chapter.id !== chapterId),
    });
  };

  const handleDeleteSection = (sectionId: string) => {
    syncMarkdown({
      ...outline,
      chapters: outline.chapters.map((chapter) => ({
        ...chapter,
        sections: chapter.sections.filter((section) => section.id !== sectionId),
      })),
    });
  };

  const handleDeleteItem = (sectionId: string, itemId: string) => {
    syncMarkdown(
      updateSectionById(sectionId, (section) => ({
        ...section,
        items: section.items.filter((item) => item.id !== itemId),
      }))
    );
  };

  const handleInsertBlankItem = (sectionId: string, itemId: string) => {
    syncMarkdown(
      updateSectionById(sectionId, (section) => {
        if (section.id !== sectionId) {
          return section;
        }

        const itemIndex = section.items.findIndex((item) => item.id === itemId);
        if (itemIndex < 0) {
          return section;
        }

        const nextItems = [...section.items];
        nextItems.splice(itemIndex + 1, 0, {
          id: `${sectionId}-new-${nextLocalIdToken()}-${itemIndex}`,
          kind: nextItems[itemIndex].kind,
          text: '',
        });
        return {
          ...section,
          items: nextItems,
        };
      })
    );
  };

  const handleAddChapter = () => {
    const nextChapter = createChapter(outline.chapters.length, nextLocalIdToken());

    setActiveChapterId(nextChapter.id);
    setActiveSectionId(nextChapter.sections[0]?.id ?? null);
    syncMarkdown({
      ...outline,
      chapters: [...outline.chapters, nextChapter],
    });
  };

  const handleAddSection = (chapterId: string, insertAfterIndex?: number) => {
    const chapter = outline.chapters.find((candidate) => candidate.id === chapterId);
    const nextSection = createSection(chapter?.sections.length ?? 0, nextLocalIdToken());

    const nextChapters = outline.chapters.map((currentChapter) => {
      if (currentChapter.id !== chapterId) {
        return currentChapter;
      }

      const nextSections = [...currentChapter.sections];

      if (typeof insertAfterIndex === 'number') {
        nextSections.splice(insertAfterIndex + 1, 0, nextSection);
      } else {
        nextSections.push(nextSection);
      }

      return {
        ...currentChapter,
        sections: nextSections,
      };
    });

    setActiveChapterId(chapterId);
    setActiveSectionId(nextSection.id);
    syncMarkdown({
      ...outline,
      chapters: nextChapters,
    });
  };

  const moveSection = (
    sourceSectionId: string,
    targetSectionId: string,
    position: 'before' | 'after'
  ) => {
    if (sourceSectionId === targetSectionId) {
      return;
    }

    const sourceEntry = findSectionEntry(sourceSectionId);
    const targetEntry = findSectionEntry(targetSectionId);

    if (!sourceEntry || !targetEntry || sourceEntry.chapter.id !== targetEntry.chapter.id) {
      return;
    }

    const movingSection = sourceEntry.section;
    const nextSections = sourceEntry.chapter.sections.filter(
      (section) => section.id !== sourceSectionId
    );
    const resolvedTargetIndex = nextSections.findIndex((section) => section.id === targetSectionId);

    if (resolvedTargetIndex < 0 || !movingSection) {
      return;
    }

    const insertIndex =
      position === 'after' ? resolvedTargetIndex + 1 : resolvedTargetIndex;
    nextSections.splice(
      Math.max(0, Math.min(insertIndex, nextSections.length)),
      0,
      movingSection
    );
    setActiveChapterId(sourceEntry.chapter.id);
    setActiveSectionId(movingSection.id);
    syncMarkdown({
      ...outline,
      chapters: outline.chapters.map((chapter) =>
        chapter.id === sourceEntry.chapter.id
          ? {
              ...chapter,
              sections: nextSections,
            }
          : chapter
      ),
    });
  };

  const handleInsertTopicAfter = (sectionId: string, topicId: string) => {
    const nextTopic = createItem(sectionId, sectionEntries.length, 'heading', nextLocalIdToken());

    syncMarkdown(
      updateSectionById(sectionId, (section) => {
        if (section.id !== sectionId) {
          return section;
        }

        const topicIndex = section.items.findIndex((item) => item.id === topicId);
        if (topicIndex < 0) {
          return section;
        }

        const nextItems = [...section.items];
        let insertIndex = topicIndex + 1;
        while (insertIndex < nextItems.length && nextItems[insertIndex].kind !== 'heading') {
          insertIndex += 1;
        }
        nextItems.splice(insertIndex, 0, nextTopic);

        return {
          ...section,
          items: nextItems,
        };
      })
    );

    setExpandedTopicIds((current) => current.filter((id) => id !== nextTopic.id));
  };

  const handleDeleteTopicGroup = (sectionId: string, topicId: string) => {
    syncMarkdown(
      updateSectionById(sectionId, (section) => {
        if (section.id !== sectionId) {
          return section;
        }

        const groupedItems = groupSectionItems(section.items);
        return {
          ...section,
          items: flattenGroupedSectionItems(
            groupedItems.looseBodyItems,
            groupedItems.topics.filter((topicGroup) => topicGroup.id !== topicId)
          ),
        };
      })
    );

    setExpandedTopicIds((current) => current.filter((id) => id !== topicId));
  };

  const handleToggleTopic = (topicId: string) => {
    setExpandedTopicIds((current) =>
      current.includes(topicId)
        ? current.filter((id) => id !== topicId)
        : [...current, topicId]
    );
  };

  const moveTopicGroup = (sourceSectionId: string, sourceTopicId: string, targetTopicId: string) => {
    if (sourceTopicId === targetTopicId) {
      return;
    }

    const sourceEntry = findSectionEntry(sourceSectionId);
    const targetEntry =
      sectionEntries.find((entry) =>
        groupSectionItems(entry.section.items).topics.some(
          (topicGroup) => topicGroup.id === targetTopicId
        )
      ) ?? null;
    const sourceSection = sourceEntry?.section;
    const targetSection = targetEntry?.section;

    if (!sourceSection || !targetSection) {
      return;
    }

    const sourceGroupedItems = groupSectionItems(sourceSection.items);
    const movingTopic = sourceGroupedItems.topics.find(
      (topicGroup) => topicGroup.id === sourceTopicId
    );

    if (!movingTopic) {
      return;
    }

    syncMarkdown({
      ...outline,
      chapters: outline.chapters.map((chapter) => ({
        ...chapter,
        sections: chapter.sections.map((section) => {
          const groupedItems = groupSectionItems(section.items);

          if (section.id === sourceSection.id && section.id === targetSection.id) {
            const reorderedTopics = groupedItems.topics.filter(
              (topicGroup) => topicGroup.id !== sourceTopicId
            );
            const targetIndex = reorderedTopics.findIndex(
              (topicGroup) => topicGroup.id === targetTopicId
            );

            if (targetIndex < 0) {
              return section;
            }

            reorderedTopics.splice(targetIndex, 0, movingTopic);
            return {
              ...section,
              items: flattenGroupedSectionItems(groupedItems.looseBodyItems, reorderedTopics),
            };
          }

          if (section.id === sourceSection.id) {
            return {
              ...section,
              items: flattenGroupedSectionItems(
                groupedItems.looseBodyItems,
                groupedItems.topics.filter((topicGroup) => topicGroup.id !== sourceTopicId)
              ),
            };
          }

          if (section.id === targetSection.id) {
            const targetIndex = groupedItems.topics.findIndex(
              (topicGroup) => topicGroup.id === targetTopicId
            );

            if (targetIndex < 0) {
              return section;
            }

            const nextTopics = [...groupedItems.topics];
            nextTopics.splice(targetIndex, 0, movingTopic);
            return {
              ...section,
              items: flattenGroupedSectionItems(groupedItems.looseBodyItems, nextTopics),
            };
          }

          return section;
        }),
      })),
    });
  };

  const handleTopicDragStart = (
    event: React.DragEvent<HTMLElement>,
    sectionId: string,
    topicId: string
  ) => {
    setDraggingTopic({ sectionId, topicId });
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData(
      OUTLINE_TOPIC_DRAG_TYPE,
      JSON.stringify({ sectionId, topicId })
    );
    event.dataTransfer.setData('text/plain', topicId);
    setOutlineDragImage(event, '[data-outline-topic-drag-preview]');
  };

  const handleTopicDrop = (
    event: React.DragEvent<HTMLElement>,
    targetTopicId: string
  ) => {
    const dragPayload = readTopicDragPayload(event) ?? draggingTopic;

    if (!dragPayload) {
      return;
    }

    moveTopicGroup(dragPayload.sectionId, dragPayload.topicId, targetTopicId);
    setDraggingTopic(null);
    setDragOverTopicId(null);
  };

  const handleSectionDragStart = (
    event: React.DragEvent<HTMLElement>,
    sectionId: string
  ) => {
    setDraggingSectionId(sectionId);
    setDraggingTopic(null);
    setDragOverTopicId(null);
    setDragOverSection(null);
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData(OUTLINE_SECTION_DRAG_TYPE, sectionId);
    event.dataTransfer.setData('text/plain', sectionId);
    setOutlineDragImage(event, '[data-outline-section-drag-preview]');
  };

  const handleSectionDrop = (
    event: React.DragEvent<HTMLElement>,
    targetSectionId: string,
    position: 'before' | 'after'
  ) => {
    const sourceSectionId =
      event.dataTransfer.getData(OUTLINE_SECTION_DRAG_TYPE) || draggingSectionId;

    if (!sourceSectionId) {
      return false;
    }

    moveSection(sourceSectionId, targetSectionId, position);
    setDraggingSectionId(null);
    setDragOverSection(null);
    return true;
  };

  const renderToolbar = () => (
    <div className="flex flex-col gap-4 border-b border-border/60 bg-surface-50/90 px-4 py-4 sm:px-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="inline-flex w-fit items-center rounded-xl border border-border/60 bg-surface-100/85 p-1">
          <button
            type="button"
            onClick={() => setActiveView('outline')}
            className={cn(
              'rounded-lg px-3 py-1.5 text-[13px] font-semibold transition-all',
              activeView === 'outline'
                ? 'bg-surface-50 text-text-main shadow-sm'
                : 'text-text-secondary hover:text-text-main'
            )}
          >
            Outline
          </button>
          <button
            type="button"
            onClick={() => setActiveView('markdown')}
            className={cn(
              'rounded-lg px-3 py-1.5 text-[13px] font-semibold transition-all',
              activeView === 'markdown'
                ? 'bg-surface-50 text-text-main shadow-sm'
                : 'text-text-secondary hover:text-text-main'
            )}
          >
            Markdown
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          {toolbarActions}
          <Tooltip title={isFullscreen ? 'Exit full screen' : 'Enter full screen'}>
            <ActionIconButton
              onClick={() => void handleFullscreenToggle()}
              className="!w-auto gap-2 whitespace-nowrap px-3"
              disabled={!allowFullscreen}
              aria-label="Full Screen"
            >
              {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              <span>Full Screen</span>
            </ActionIconButton>
          </Tooltip>
          <ActionIconButton
            onClick={handleDownload}
            className="!w-auto gap-2 whitespace-nowrap px-3"
          >
            <DownloadOutlined />
            <span>Download</span>
          </ActionIconButton>
          <ActionIconButton
            onClick={() => void onRefresh?.()}
            className="!w-auto gap-2 whitespace-nowrap px-3"
            disabled={!canRefresh || refreshing}
          >
            <ReloadOutlined className={refreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </ActionIconButton>
        </div>
      </div>

      {activeView === 'outline' && (
        <div className="rounded-2xl border border-border/60 bg-surface-50 px-4 py-3 shadow-[0_10px_24px_rgba(15,23,42,0.04)]">
          <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-text-secondary">
            <OrderedListOutlined />
            Presentation Title
          </div>
          <Input
            value={outline.presentationTitle}
            onChange={(event) => handlePresentationTitleChange(event.target.value)}
            placeholder="Enter presentation title"
            className="!h-10 !rounded-xl !border-border/60 !bg-surface-50 !text-[15px] !font-semibold !text-text-main"
          />
        </div>
      )}
    </div>
  );

  return (
    <div
      ref={rootRef}
      className={cn(
        'outline-editor-shell w-full',
        isFullscreen && 'flex h-full flex-col bg-surface-50',
        isPseudoFullscreen &&
          'fixed inset-4 z-50 flex flex-col rounded-[28px] bg-surface-50 shadow-[0_24px_60px_rgba(15,23,42,0.14)]'
      )}
    >
      <div
        className={cn(
          'overflow-hidden rounded-[28px] border border-border/70 bg-surface-50 shadow-[0_16px_40px_rgba(15,23,42,0.08)]',
          isFullscreen && 'flex min-h-0 flex-1 flex-col'
        )}
      >
        {renderToolbar()}

        <div
          className={cn(
            'px-4 py-4 sm:px-5',
            isFullscreen ? 'min-h-0 flex-1 overflow-y-auto' : 'max-h-[100vh] overflow-y-auto'
          )}
        >
          {activeView === 'markdown' ? (
            <div className="rounded-[24px] border border-border/70 bg-surface-50 px-4 py-4 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
              <div className="mb-3 flex items-center justify-between gap-3">
                <span className="text-xs font-semibold uppercase tracking-[0.22em] text-text-secondary">
                  Markdown Source
                </span>
                <span className="text-[12px] text-text-secondary/70">Raw markdown preview</span>
              </div>
              <div className="rounded-2xl border border-border/70 bg-surface-50 px-4 py-4">
                <pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-6 text-text-main">
                  {currentMarkdown || '# Empty markdown'}
                </pre>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {outline.chapters.length > 0 && (
                <>
                  <div className="overflow-hidden rounded-2xl border border-border/70 bg-surface-50">
                    <div className="flex min-w-0 items-center gap-2.5 bg-surface-100/55 px-3 py-3">
                      <span className="w-7 shrink-0 text-center text-[17px] font-semibold text-brand-strong">
                        1
                      </span>
                      <span className="h-8 w-px bg-border/70" />
                      <span className="w-20 shrink-0 text-[14px] font-semibold text-text-main">
                        Cover
                      </span>
                      <Input
                        value={outline.presentationTitle}
                        onChange={(event) => handlePresentationTitleChange(event.target.value)}
                        placeholder="Presentation title"
                        className="!h-8 flex-1 !rounded-lg !border-0 !bg-transparent !px-0 !text-[15px] !font-semibold !text-text-main"
                      />
                    </div>
                  </div>

                  <div className="overflow-hidden rounded-2xl border border-border/70 bg-surface-50">
                    <div className="flex min-w-0 items-center gap-2.5 bg-surface-100/55 px-3 py-3">
                      <span className="w-7 shrink-0 text-center text-[17px] font-semibold text-brand-strong">
                        2
                      </span>
                      <span className="h-8 w-px bg-border/70" />
                      <span className="text-[14px] font-semibold text-text-main">Catalog</span>
                    </div>
                    <div className="space-y-2 px-4 py-4 sm:px-[8.125rem]">
                      {catalogItems.map((catalogItem) => (
                        <div
                          key={catalogItem.id}
                          className="group/catalog flex min-h-10 items-center gap-3 rounded-lg px-2 py-1 transition-colors hover:bg-surface-100/60"
                        >
                          <span className="w-20 shrink-0 text-[13px] font-semibold text-text-secondary">
                            {catalogItem.label}
                          </span>
                          <Input
                            value={catalogItem.title}
                            onChange={(event) =>
                              handleCatalogItemTitleChange(catalogItem, event.target.value)
                            }
                            placeholder={`Chapter ${catalogItem.chapterNumber} title`}
                            className="!h-8 flex-1 !rounded-lg !border-0 !bg-transparent !px-0 !text-[15px] !font-semibold !text-text-main"
                            aria-label={`Edit catalog item ${catalogItem.chapterNumber}`}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {outline.chapters.map((chapter, chapterIndex) => (
                <div
                  key={chapter.id}
                  className={cn(
                    'overflow-hidden rounded-2xl border border-border/70 bg-surface-50',
                    resolvedActiveChapterId === chapter.id && 'border-brand-border'
                  )}
                >
                  <div className="flex flex-col gap-2 border-b border-border/60 bg-surface-100/65 px-3 py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex min-w-0 flex-1 items-center gap-2.5">
                      <span className="w-7 shrink-0 text-center text-[17px] font-semibold text-brand-strong">
                        {chapterIndex + 3}
                      </span>
                      <span className="h-8 w-px bg-border/70" />
                      <span className="text-[14px] font-semibold text-text-main">Chapter</span>
                      <Input
                        value={chapter.title}
                        onChange={(event) =>
                          handleChapterTitleChange(chapter.id, event.target.value)
                        }
                        placeholder="Chapter title"
                        className="!h-8 flex-1 !rounded-lg !border-0 !bg-transparent !px-0 !text-[15px] !font-semibold !text-text-main"
                      />
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Tooltip title="Add section">
                        <ActionIconButton
                          variant="compact"
                          onClick={(event) => {
                            event.stopPropagation();
                            handleAddSection(chapter.id);
                          }}
                          aria-label={`Add section to ${chapter.title || 'chapter'}`}
                        >
                          <PlusOutlined />
                        </ActionIconButton>
                      </Tooltip>
                      <Tooltip title="Delete chapter">
                        <ActionIconButton
                          danger
                          variant="compact"
                          onClick={(event) => {
                            event.stopPropagation();
                            handleDeleteChapter(chapter.id);
                          }}
                          aria-label={`Delete ${chapter.title || 'chapter'}`}
                        >
                          <DeleteOutlined />
                        </ActionIconButton>
                      </Tooltip>
                    </div>
                  </div>

                  <div className="space-y-2 px-2 py-2 sm:px-3">
                    {chapter.sections.map((section, index) => {
                      const isActive = resolvedActiveSectionId === section.id;
                      const groupedItems = groupSectionItems(section.items);
                      const isDraggingSection = draggingSectionId === section.id;
                      const isSectionDragTarget =
                        dragOverSection?.sectionId === section.id && draggingSectionId !== section.id;

                      return (
                        <div
                          key={section.id}
                          data-outline-section-drag-preview={section.id}
                          className={cn(
                            'group overflow-hidden rounded-xl border bg-surface-50 transition-all duration-200',
                            isActive
                              ? 'border-brand-border shadow-[0_0_0_1px_rgba(49,95,143,0.14)]'
                              : 'border-border/70 hover:border-brand-border',
                            isSectionDragTarget && 'border-brand-border bg-brand-surface/35',
                            isSectionDragTarget &&
                              dragOverSection?.position === 'before' &&
                              'shadow-[inset_0_2px_0_rgba(49,95,143,0.65)]',
                            isSectionDragTarget &&
                              dragOverSection?.position === 'after' &&
                              'shadow-[inset_0_-2px_0_rgba(49,95,143,0.65)]',
                            isDraggingSection && 'opacity-60'
                          )}
                          onClick={() => {
                            setActiveChapterId(chapter.id);
                            setActiveSectionId(section.id);
                          }}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault();
                              setActiveChapterId(chapter.id);
                              setActiveSectionId(section.id);
                            }
                          }}
                          role="button"
                          tabIndex={0}
                          aria-pressed={isActive}
                          onDragOver={(event) => {
                            const isSectionDrag =
                              hasDragType(event, OUTLINE_SECTION_DRAG_TYPE) ||
                              !!draggingSectionId;

                            if (!isSectionDrag) {
                              return;
                            }

                            const position = getSectionDropPosition(event, section.id);

                            event.preventDefault();
                            event.dataTransfer.dropEffect = 'move';
                            setDragOverSection({ sectionId: section.id, position });
                          }}
                          onDragLeave={() => setDragOverSection(null)}
                          onDrop={(event) => {
                            if (
                              !hasDragType(event, OUTLINE_SECTION_DRAG_TYPE) &&
                              !draggingSectionId
                            ) {
                              return;
                            }

                            event.preventDefault();
                            event.stopPropagation();
                            handleSectionDrop(
                              event,
                              section.id,
                              getSectionDropPosition(event, section.id)
                            );
                          }}
                        >
                          <div className="flex flex-col gap-2 border-b border-border/50 bg-surface-100/55 px-3 py-2 sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex min-w-0 flex-1 items-center gap-2.5">
                              <button
                                type="button"
                                draggable
                                onDragStart={(event) => handleSectionDragStart(event, section.id)}
                                onDragEnd={() => {
                                  setDraggingSectionId(null);
                                  setDragOverSection(null);
                                }}
                                onClick={(event) => event.stopPropagation()}
                                className="flex h-8 w-7 shrink-0 cursor-grab items-center justify-center text-text-secondary transition-colors active:cursor-grabbing hover:text-text-main"
                                aria-label={`Drag ${section.title || 'section'}`}
                              >
                                <HolderOutlined />
                              </button>
                              <span className="w-7 shrink-0 text-center text-[17px] font-semibold text-brand-strong">
                                {index + 1}
                              </span>
                              <span className="h-8 w-px bg-border/70" />
                              <span className="text-[14px] font-semibold text-text-main">
                                Section
                              </span>
                              <Input
                                value={section.title}
                                onChange={(event) =>
                                  handleSectionTitleChange(section.id, event.target.value)
                                }
                                placeholder="Section title"
                                className="!h-8 flex-1 !rounded-lg !border-0 !bg-transparent !px-0 !text-[15px] !font-semibold !text-text-main"
                              />
                            </div>

                            <div className="flex flex-wrap items-center gap-1.5">
                              <Tooltip title="Add section below">
                                <ActionIconButton
                                  variant="compact"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    handleAddSection(chapter.id, index);
                                  }}
                                  aria-label={`Add section below ${section.title}`}
                                >
                                  <PlusOutlined />
                                </ActionIconButton>
                              </Tooltip>
                              <Tooltip title="Delete section">
                                <ActionIconButton
                                  danger
                                  variant="compact"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    handleDeleteSection(section.id);
                                  }}
                                  aria-label={`Delete ${section.title}`}
                                >
                                  <DeleteOutlined />
                                </ActionIconButton>
                              </Tooltip>
                            </div>
                          </div>

                          <div className="px-2 py-2 sm:px-3">
                            {groupedItems.looseBodyItems.length > 0 ? (
                              <div className="mb-1 space-y-0.5">
                                {groupedItems.looseBodyItems.map((item) => (
                                  <div
                                    key={item.id}
                                    className="group/body flex min-h-9 items-center gap-3 rounded-lg px-2 py-1 text-text-secondary transition-colors hover:bg-surface-100/70 sm:pl-[6.25rem]"
                                  >
                                    <span className="w-14 shrink-0 text-[12px] font-medium text-text-secondary">
                                      Body
                                    </span>
                                    <TextArea
                                      value={item.text}
                                      onChange={(event) =>
                                        handleItemTextChange(section.id, item.id, event.target.value)
                                      }
                                      autoSize={{ minRows: 1 }}
                                      placeholder="Body point"
                                      className="!min-h-8 flex-1 !resize-none !rounded-lg !border-0 !bg-transparent !px-0 !py-1 !text-[13px] !leading-5 !text-text-secondary !shadow-none"
                                    />
                                    <div className="flex items-center gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover/body:opacity-100">
                                      <Tooltip title="Delete body">
                                        <ActionIconButton
                                          danger
                                          variant="compact"
                                          onClick={(event) => {
                                            event.stopPropagation();
                                            handleDeleteItem(section.id, item.id);
                                          }}
                                          aria-label={`Delete ${item.text || 'body point'}`}
                                        >
                                          <DeleteOutlined />
                                        </ActionIconButton>
                                      </Tooltip>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : null}

                            <div className="space-y-0.5">
                              {groupedItems.topics.map((topicGroup) => {
                                const isTopicExpanded = expandedTopicIds.includes(topicGroup.id);
                                const isDragging = draggingTopic?.topicId === topicGroup.id;
                                const isDragTarget =
                                  dragOverTopicId === topicGroup.id &&
                                  draggingTopic?.topicId !== topicGroup.id;

                                return (
                                  <div
                                    data-outline-topic-drag-preview={topicGroup.id}
                                    key={topicGroup.id}
                                    className={cn(
                                      'rounded-xl transition-colors',
                                      isDragTarget && 'bg-brand-surface/70',
                                      isDragging && 'opacity-50'
                                    )}
                                    onDragOver={(event) => {
                                      const isTopicDrag =
                                        hasDragType(event, OUTLINE_TOPIC_DRAG_TYPE) ||
                                        !!draggingTopic;

                                      if (!isTopicDrag) {
                                        return;
                                      }

                                      event.preventDefault();
                                      event.stopPropagation();
                                      event.dataTransfer.dropEffect = 'move';
                                      setDragOverTopicId(topicGroup.id);
                                    }}
                                    onDragLeave={() => setDragOverTopicId(null)}
                                    onDrop={(event) => {
                                      if (
                                        !hasDragType(event, OUTLINE_TOPIC_DRAG_TYPE) &&
                                        !draggingTopic
                                      ) {
                                        return;
                                      }

                                      event.preventDefault();
                                      event.stopPropagation();
                                      handleTopicDrop(event, topicGroup.id);
                                    }}
                                  >
                                    <div
                                      className={cn(
                                        'group/topic flex min-h-10 items-center gap-2.5 rounded-lg px-2 py-1 transition-colors',
                                        isTopicExpanded ? 'bg-surface-100/80' : 'hover:bg-surface-100/65'
                                      )}
                                    >
                                      <button
                                        type="button"
                                        draggable
                                        onDragStart={(event) =>
                                          handleTopicDragStart(event, section.id, topicGroup.id)
                                        }
                                        onDragEnd={() => {
                                          setDraggingTopic(null);
                                          setDragOverTopicId(null);
                                        }}
                                        onClick={(event) => event.stopPropagation()}
                                        className="flex h-8 w-7 shrink-0 cursor-grab items-center justify-center text-text-secondary transition-colors active:cursor-grabbing hover:text-text-main"
                                        aria-label={`Drag ${topicGroup.topic.text || 'topic'}`}
                                      >
                                        <HolderOutlined />
                                      </button>
                                      <button
                                        type="button"
                                        onClick={(event) => {
                                          event.stopPropagation();
                                          handleToggleTopic(topicGroup.id);
                                        }}
                                        className="flex h-8 w-7 shrink-0 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-surface-50 hover:text-text-main"
                                        aria-expanded={isTopicExpanded}
                                        aria-label={
                                          isTopicExpanded
                                            ? `Collapse ${topicGroup.topic.text || 'topic'}`
                                            : `Expand ${topicGroup.topic.text || 'topic'}`
                                        }
                                      >
                                        {isTopicExpanded ? <CaretDownOutlined /> : <CaretRightOutlined />}
                                      </button>
                                      <span className="w-14 shrink-0 text-left text-[12px] font-medium text-text-secondary">
                                        Topic
                                      </span>
                                      <Input
                                        value={topicGroup.topic.text}
                                        onChange={(event) =>
                                          handleItemTextChange(
                                            section.id,
                                            topicGroup.topic.id,
                                            event.target.value
                                          )
                                        }
                                        placeholder="Topic"
                                        className="!h-8 flex-1 !rounded-lg !border-0 !bg-transparent !px-0 !text-[14px] !font-semibold !text-text-main"
                                      />
                                      <div className="flex items-center gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover/topic:opacity-100">
                                        <Tooltip title="Add topic">
                                          <ActionIconButton
                                            variant="compact"
                                            onClick={(event) => {
                                              event.stopPropagation();
                                              handleInsertTopicAfter(section.id, topicGroup.id);
                                            }}
                                            aria-label={`Add topic below ${topicGroup.topic.text || 'topic'}`}
                                          >
                                            <PlusOutlined />
                                          </ActionIconButton>
                                        </Tooltip>
                                        <Tooltip title="Delete topic">
                                          <ActionIconButton
                                            danger
                                            variant="compact"
                                            onClick={(event) => {
                                              event.stopPropagation();
                                              handleDeleteTopicGroup(section.id, topicGroup.id);
                                            }}
                                            aria-label={`Delete ${topicGroup.topic.text || 'topic'}`}
                                          >
                                            <DeleteOutlined />
                                          </ActionIconButton>
                                        </Tooltip>
                                      </div>
                                    </div>

                                    {isTopicExpanded ? (
                                      <div className="space-y-0.5 pb-1 pl-[6.25rem] pr-2">
                                        {topicGroup.bodyItems.length > 0 ? (
                                          topicGroup.bodyItems.map((item) => (
                                            <div
                                              key={item.id}
                                              className="group/body flex min-h-9 items-start gap-3 rounded-lg px-2 py-1 text-text-secondary transition-colors hover:bg-surface-100/55"
                                            >
                                              <span className="w-14 shrink-0 pt-1 text-[12px] font-medium text-text-secondary">
                                                Body
                                              </span>
                                              <TextArea
                                                value={item.text}
                                                onChange={(event) =>
                                                  handleItemTextChange(
                                                    section.id,
                                                    item.id,
                                                    event.target.value
                                                  )
                                                }
                                                autoSize={{ minRows: 1 }}
                                                placeholder="Body point"
                                                className="!min-h-8 flex-1 !resize-none !rounded-lg !border-0 !bg-transparent !px-0 !py-1 !text-[13px] !leading-5 !text-text-secondary !shadow-none"
                                              />
                                              <div className="flex items-center gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover/body:opacity-100">
                                                <Tooltip title="Add body below">
                                                  <ActionIconButton
                                                    variant="compact"
                                                    onClick={(event) => {
                                                      event.stopPropagation();
                                                      handleInsertBlankItem(section.id, item.id);
                                                    }}
                                                    aria-label={`Add body after ${item.text || 'current body'}`}
                                                  >
                                                    <PlusOutlined />
                                                  </ActionIconButton>
                                                </Tooltip>
                                                <Tooltip title="Delete body">
                                                  <ActionIconButton
                                                    danger
                                                    variant="compact"
                                                    onClick={(event) => {
                                                      event.stopPropagation();
                                                      handleDeleteItem(section.id, item.id);
                                                    }}
                                                    aria-label={`Delete ${item.text || 'body point'}`}
                                                  >
                                                    <DeleteOutlined />
                                                  </ActionIconButton>
                                                </Tooltip>
                                              </div>
                                            </div>
                                          ))
                                        ) : (
                                          <div className="rounded-lg px-2 py-1.5 text-[12px] text-text-secondary/70">
                                            No body points yet.
                                          </div>
                                        )}
                                      </div>
                                    ) : null}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}

              {outline.chapters.length === 0 && (
                <div className="rounded-[24px] border border-dashed border-border/70 bg-surface-100/55 px-6 py-10 text-center">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-surface text-brand-strong">
                    <OrderedListOutlined className="text-lg" />
                  </div>
                  <p className="text-[15px] font-semibold text-text-main">No chapters yet</p>
                  <p className="mt-2 text-[13px] text-text-secondary">
                    Generate markdown first, or create the first chapter manually.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleAddChapter()}
                    className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-full bg-primary-500 px-4 text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
                  >
                    <PlusOutlined />
                    <span>Add First Chapter</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
