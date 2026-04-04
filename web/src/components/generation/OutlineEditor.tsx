import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Input, Tooltip } from 'antd';
import {
  CaretDownOutlined,
  CaretRightOutlined,
  CopyOutlined,
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
import type {
  OutlineDocument,
  OutlineItem,
  OutlineItemKind,
  OutlineSection,
} from './outlineModel';
import { parseMarkdownToOutline, serializeOutlineToMarkdown } from './outlineModel';

interface OutlineEditorProps {
  value: string;
  onChange: (value: string) => void;
  onRefresh?: () => void | Promise<void>;
  refreshDisabled?: boolean;
  refreshing?: boolean;
  allowFullscreen?: boolean;
}

const EMPTY_OUTLINE: OutlineDocument = {
  presentationTitle: '',
  sections: [],
};

const createSection = (index: number): OutlineSection => ({
  id: `section-local-${Date.now()}-${index}`,
  kind: 'section',
  title: `Section ${index + 1}`,
  items: [
    {
      id: `item-local-${Date.now()}-${index}-0`,
      kind: 'heading',
      text: 'New topic',
    },
  ],
});

const createItem = (sectionId: string, index: number, kind: OutlineItemKind): OutlineItem => ({
  id: `${sectionId}-${kind}-${Date.now()}-${index}`,
  kind,
  text: kind === 'heading' ? 'New topic' : 'New body point',
});

const cloneSection = (section: OutlineSection, index: number): OutlineSection => ({
  id: `section-clone-${Date.now()}-${index}`,
  kind: 'section',
  title: `${section.title} Copy`,
  items: section.items.map((item, itemIndex) => ({
    ...item,
    id: `item-clone-${Date.now()}-${index}-${itemIndex}`,
  })),
});

const toDownloadFilename = (title: string) => {
  const normalized = title
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

  return `${normalized || 'outline'}.md`;
};

const iconButtonClassName =
  'inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-surface-50 text-[13px] text-text-secondary transition-colors hover:border-primary-400/60 hover:text-primary-500 disabled:cursor-not-allowed disabled:opacity-40 sm:h-9 sm:w-9';

const smallActionClassName =
  'inline-flex min-h-10 items-center gap-1 rounded-lg border border-border/60 bg-surface-50 px-3 text-[12px] font-medium text-text-secondary transition-colors hover:border-primary-400/60 hover:text-primary-500';

export const OutlineEditor: React.FC<OutlineEditorProps> = ({
  value,
  onChange,
  onRefresh,
  refreshDisabled = false,
  refreshing = false,
  allowFullscreen = true,
}) => {
  const [activeView, setActiveView] = useState<'outline' | 'markdown'>('outline');
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [collapsedSectionIds, setCollapsedSectionIds] = useState<string[]>([]);
  const [isPseudoFullscreen, setIsPseudoFullscreen] = useState(false);
  const [isBrowserFullscreen, setIsBrowserFullscreen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const outline = useMemo<OutlineDocument>(
    () => (value.trim() ? parseMarkdownToOutline(value) : EMPTY_OUTLINE),
    [value]
  );
  const resolvedActiveSectionId =
    activeSectionId && outline.sections.some((section) => section.id === activeSectionId)
      ? activeSectionId
      : outline.sections[0]?.id ?? null;
  const currentMarkdown = serializeOutlineToMarkdown(outline);
  const canRefresh = !!onRefresh && !refreshDisabled;
  const isFullscreen = isBrowserFullscreen || isPseudoFullscreen;

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
    onChange(serializeOutlineToMarkdown(nextOutline));
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
    syncMarkdown({
      ...outline,
      sections: outline.sections.map((section) =>
        section.id === sectionId ? { ...section, title } : section
      ),
    });
  };

  const handleItemTextChange = (sectionId: string, itemId: string, text: string) => {
    syncMarkdown({
      ...outline,
      sections: outline.sections.map((section) =>
        section.id === sectionId
          ? {
              ...section,
              items: section.items.map((item) =>
                item.id === itemId ? { ...item, text } : item
              ),
            }
          : section
      ),
    });
  };

  const handleItemKindToggle = (sectionId: string, itemId: string) => {
    syncMarkdown({
      ...outline,
      sections: outline.sections.map((section) =>
        section.id === sectionId
          ? {
              ...section,
              items: section.items.map((item) =>
                item.id === itemId
                  ? {
                      ...item,
                      kind: item.kind === 'heading' ? 'bullet' : 'heading',
                    }
                  : item
              ),
            }
          : section
      ),
    });
  };

  const handleDeleteSection = (sectionId: string) => {
    syncMarkdown({
      ...outline,
      sections: outline.sections.filter((section) => section.id !== sectionId),
    });
  };

  const handleDeleteItem = (sectionId: string, itemId: string) => {
    syncMarkdown({
      ...outline,
      sections: outline.sections.map((section) =>
        section.id === sectionId
          ? {
              ...section,
              items: section.items.filter((item) => item.id !== itemId),
            }
          : section
      ),
    });
  };

  const handleDuplicateSection = (sectionId: string) => {
    const sectionIndex = outline.sections.findIndex((section) => section.id === sectionId);
    if (sectionIndex < 0) {
      return;
    }

    const nextSections = [...outline.sections];
    nextSections.splice(sectionIndex + 1, 0, cloneSection(nextSections[sectionIndex], sectionIndex));
    syncMarkdown({
      ...outline,
      sections: nextSections,
    });
  };

  const handleInsertBlankItem = (sectionId: string, itemId: string) => {
    syncMarkdown({
      ...outline,
      sections: outline.sections.map((section) => {
        if (section.id !== sectionId) {
          return section;
        }

        const itemIndex = section.items.findIndex((item) => item.id === itemId);
        if (itemIndex < 0) {
          return section;
        }

        const nextItems = [...section.items];
        nextItems.splice(itemIndex + 1, 0, {
          id: `${sectionId}-new-${Date.now()}-${itemIndex}`,
          kind: nextItems[itemIndex].kind,
          text: '',
        });
        return {
          ...section,
          items: nextItems,
        };
      }),
    });
  };

  const handleAddSection = (insertAfterIndex?: number) => {
    const nextSection = createSection(outline.sections.length);
    const nextSections = [...outline.sections];

    if (typeof insertAfterIndex === 'number') {
      nextSections.splice(insertAfterIndex + 1, 0, nextSection);
    } else {
      nextSections.push(nextSection);
    }

    setActiveSectionId(nextSection.id);
    syncMarkdown({
      ...outline,
      sections: nextSections,
    });
  };

  const handleAddItem = (sectionId: string, kind: OutlineItemKind) => {
    syncMarkdown({
      ...outline,
      sections: outline.sections.map((section) =>
        section.id === sectionId
          ? {
              ...section,
              items: [...section.items, createItem(sectionId, section.items.length, kind)],
            }
          : section
      ),
    });
  };

  const handleToggleSection = (sectionId: string) => {
    setCollapsedSectionIds((current) =>
      current.includes(sectionId)
        ? current.filter((id) => id !== sectionId)
        : [...current, sectionId]
    );
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
          <Tooltip title={isFullscreen ? 'Exit full screen' : 'Enter full screen'}>
            <button
              type="button"
              onClick={() => void handleFullscreenToggle()}
              className={cn(iconButtonClassName, '!w-auto gap-2 whitespace-nowrap px-3')}
              disabled={!allowFullscreen}
              aria-label="Full Screen"
            >
              {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              <span>Full Screen</span>
            </button>
          </Tooltip>
          <button
            type="button"
            onClick={handleDownload}
            className={cn(iconButtonClassName, '!w-auto gap-2 whitespace-nowrap px-3')}
          >
            <DownloadOutlined />
            <span>Download</span>
          </button>
          <button
            type="button"
            onClick={() => void onRefresh?.()}
            className={cn(iconButtonClassName, '!w-auto gap-2 whitespace-nowrap px-3')}
            disabled={!canRefresh || refreshing}
          >
            <ReloadOutlined className={refreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
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
          'fixed inset-4 z-50 flex flex-col rounded-[28px] bg-surface-50 shadow-[0_40px_120px_rgba(15,23,42,0.18)]'
      )}
    >
      <div
        className={cn(
          'overflow-hidden rounded-[28px] border border-border/70 bg-surface-50/95 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl',
          isFullscreen && 'flex min-h-0 flex-1 flex-col'
        )}
      >
        {renderToolbar()}

        <div
          className={cn(
            'px-4 py-4 sm:px-5',
            isFullscreen ? 'min-h-0 flex-1 overflow-y-auto' : 'max-h-[70vh] overflow-y-auto'
          )}
        >
          {activeView === 'markdown' ? (
            <div className="rounded-[24px] border border-border/70 bg-surface-50 px-4 py-4 shadow-[0_10px_30px_rgba(15,23,42,0.06)]">
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
            <div className="space-y-4">
              {outline.sections.map((section, index) => {
                const isActive = resolvedActiveSectionId === section.id;
                const isCollapsed = collapsedSectionIds.includes(section.id);

                return (
                  <div key={section.id} className="space-y-2">
                    <div
                      className={cn(
                        'group overflow-hidden rounded-[24px] border bg-surface-50 shadow-[0_10px_24px_rgba(15,23,42,0.04)] transition-all duration-200',
                        isActive
                          ? 'border-primary-500/80 shadow-[0_0_0_1px_rgba(139,92,246,0.18)]'
                          : 'border-border/70 hover:border-primary-400/45'
                      )}
                      onClick={() => setActiveSectionId(section.id)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          setActiveSectionId(section.id);
                        }
                      }}
                      role="button"
                      tabIndex={0}
                      aria-pressed={isActive}
                    >
                      <div className="flex flex-col gap-3 border-b border-border/60 bg-surface-100/55 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex min-w-0 items-center gap-3">
                          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-50 text-text-secondary">
                            <HolderOutlined />
                          </span>
                          <span className="text-[20px] font-semibold text-primary-500">
                            {index + 1}
                          </span>
                          <span className="rounded-full border border-primary-500/15 bg-primary-500/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-500">
                            Section
                          </span>
                          <Input
                            value={section.title}
                            onChange={(event) =>
                              handleSectionTitleChange(section.id, event.target.value)
                            }
                            placeholder="Section title"
                            className="!h-9 min-w-0 flex-1 !rounded-xl !border-0 !bg-transparent !px-0 !text-[15px] !font-semibold !text-text-main"
                          />
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          <Tooltip title="Add topic">
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation();
                                handleAddItem(section.id, 'heading');
                              }}
                              className={iconButtonClassName}
                              aria-label={`Add topic to ${section.title}`}
                            >
                              <PlusOutlined />
                            </button>
                          </Tooltip>
                          <Tooltip title="Duplicate section">
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation();
                                handleDuplicateSection(section.id);
                              }}
                              className={iconButtonClassName}
                              aria-label={`Duplicate ${section.title}`}
                            >
                              <CopyOutlined />
                            </button>
                          </Tooltip>
                          <Tooltip title={isCollapsed ? 'Expand section' : 'Collapse section'}>
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation();
                                handleToggleSection(section.id);
                              }}
                              className={iconButtonClassName}
                              aria-label={
                                isCollapsed
                                  ? `Expand ${section.title}`
                                  : `Collapse ${section.title}`
                              }
                            >
                              {isCollapsed ? <CaretRightOutlined /> : <CaretDownOutlined />}
                            </button>
                          </Tooltip>
                          <Tooltip title="Delete section">
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation();
                                handleDeleteSection(section.id);
                              }}
                              className={cn(iconButtonClassName, 'hover:text-red-500')}
                              aria-label={`Delete ${section.title}`}
                            >
                              <DeleteOutlined />
                            </button>
                          </Tooltip>
                        </div>
                      </div>

                      {!isCollapsed && (
                        <div className="space-y-2 px-3 py-3 sm:px-4">
                          {section.items.map((item) => (
                            <div
                              key={item.id}
                              className="group/item flex flex-col gap-2 rounded-2xl border border-border/55 bg-surface-50/90 px-3 py-2.5 sm:flex-row sm:items-center"
                            >
                              <div className="flex items-center gap-2 sm:w-[128px]">
                                <span className="ml-1 h-2 w-2 rounded-full bg-primary-500/45" />
                                <button
                                  type="button"
                                  onClick={() => handleItemKindToggle(section.id, item.id)}
                                  className={cn(
                                    'min-h-10 rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.14em] transition-colors',
                                    item.kind === 'heading'
                                      ? 'bg-primary-500/12 text-primary-500'
                                      : 'bg-surface-100 text-text-secondary'
                                  )}
                                >
                                  {item.kind === 'heading' ? 'Topic' : 'Body'}
                                </button>
                              </div>
                              <Input
                                value={item.text}
                                onChange={(event) =>
                                  handleItemTextChange(section.id, item.id, event.target.value)
                                }
                                placeholder="Outline content"
                                className="!h-9 flex-1 !rounded-xl !border-0 !bg-transparent !px-0 !text-[13px] !text-text-main"
                              />
                              <div className="flex items-center gap-2 opacity-100 transition-opacity sm:opacity-0 sm:group-hover/item:opacity-100">
                                <Tooltip title="Add row">
                                  <button
                                    type="button"
                                    onClick={() => handleInsertBlankItem(section.id, item.id)}
                                    className={iconButtonClassName}
                                    aria-label={`Add row after ${item.text || 'current item'}`}
                                  >
                                    <PlusOutlined />
                                  </button>
                                </Tooltip>
                                <Tooltip title="Delete row">
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteItem(section.id, item.id)}
                                    className={cn(iconButtonClassName, 'hover:text-red-500')}
                                    aria-label={`Delete ${item.text || 'current item'}`}
                                  >
                                    <DeleteOutlined />
                                  </button>
                                </Tooltip>
                              </div>
                            </div>
                          ))}

                          <div className="flex flex-wrap gap-2 pt-1">
                            <button
                              type="button"
                              onClick={() => handleAddItem(section.id, 'heading')}
                              className={smallActionClassName}
                            >
                              <PlusOutlined />
                              <span>Add Topic</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleAddItem(section.id, 'bullet')}
                              className={smallActionClassName}
                            >
                              <PlusOutlined />
                              <span>Add Body</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex justify-center">
                      <button
                        type="button"
                        onClick={() => handleAddSection(index)}
                        className="inline-flex min-h-10 items-center gap-2 rounded-full border border-dashed border-border/70 bg-surface-50 px-4 text-[12px] font-medium text-text-secondary transition-colors hover:border-primary-400/60 hover:text-primary-500"
                      >
                        <PlusOutlined />
                        <span>Add Section Below</span>
                      </button>
                    </div>
                  </div>
                );
              })}

              {outline.sections.length === 0 && (
                <div className="rounded-[24px] border border-dashed border-border/70 bg-surface-100/55 px-6 py-10 text-center">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-500/12 text-primary-500">
                    <OrderedListOutlined className="text-lg" />
                  </div>
                  <p className="text-[15px] font-semibold text-text-main">No sections yet</p>
                  <p className="mt-2 text-[13px] text-text-secondary">
                    Generate markdown first, or create the first section manually.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleAddSection()}
                    className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-full bg-primary-500 px-4 text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
                  >
                    <PlusOutlined />
                    <span>Add First Section</span>
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
