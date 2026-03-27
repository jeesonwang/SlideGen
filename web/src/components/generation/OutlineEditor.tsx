import React, { useEffect, useRef, useState } from 'react';
import { Button, Input, Tooltip } from 'antd';
import {
  CopyOutlined,
  DeleteOutlined,
  OrderedListOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { cn } from '../../utils/classnames';
import type { OutlineDocument, OutlineItemKind } from './outlineModel';
import { parseMarkdownToOutline, serializeOutlineToMarkdown } from './outlineModel';

interface OutlineEditorProps {
  value: string;
  onChange: (value: string) => void;
}

const EMPTY_OUTLINE: OutlineDocument = {
  presentationTitle: '',
  sections: [],
};

const createSection = (index: number) => ({
  id: `section-local-${Date.now()}-${index}`,
  kind: 'section' as const,
  title: `Section ${index + 1}`,
  items: [
    {
      id: `item-local-${Date.now()}-${index}-0`,
      kind: 'heading' as const,
      text: 'New topic',
    },
  ],
});

const createItem = (sectionId: string, index: number, kind: OutlineItemKind) => ({
  id: `${sectionId}-${kind}-${Date.now()}-${index}`,
  kind,
  text: kind === 'heading' ? 'New topic' : 'New bullet',
});

export const OutlineEditor: React.FC<OutlineEditorProps> = ({ value, onChange }) => {
  const [outline, setOutline] = useState<OutlineDocument>(EMPTY_OUTLINE);
  const [activeView, setActiveView] = useState<'outline' | 'markdown'>('outline');
  const isInternalUpdate = useRef(false);
  const currentMarkdown = serializeOutlineToMarkdown(outline);

  useEffect(() => {
    if (isInternalUpdate.current) {
      isInternalUpdate.current = false;
      return;
    }

    setOutline(parseMarkdownToOutline(value));
  }, [value]);

  const syncMarkdown = (nextOutline: OutlineDocument) => {
    setOutline(nextOutline);
    isInternalUpdate.current = true;
    onChange(serializeOutlineToMarkdown(nextOutline));
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(currentMarkdown);
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

  const handleAddSection = (insertAfterIndex?: number) => {
    const nextSection = createSection(outline.sections.length);
    const nextSections = [...outline.sections];

    if (typeof insertAfterIndex === 'number') {
      nextSections.splice(insertAfterIndex + 1, 0, nextSection);
    } else {
      nextSections.push(nextSection);
    }

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

  return (
    <div className="w-full">
      <div
        className={cn(
          'overflow-hidden rounded-[30px] border border-border/70 bg-surface-50/95 shadow-[0_24px_80px_rgba(15,23,42,0.08)]',
          'backdrop-blur-xl'
        )}
      >
        <div className="flex flex-col gap-4 border-b border-border/60 bg-surface-50/85 px-5 py-5 sm:px-7">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="inline-flex w-fit items-center rounded-2xl bg-surface-100/90 p-1">
              <button
                type="button"
                onClick={() => setActiveView('outline')}
                className={cn(
                  'min-h-11 rounded-xl px-5 text-sm font-semibold transition-all',
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
                  'min-h-11 rounded-xl px-5 text-sm font-semibold transition-all',
                  activeView === 'markdown'
                    ? 'bg-surface-50 text-text-main shadow-sm'
                    : 'text-text-secondary hover:text-text-main'
                )}
              >
                Markdown
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-primary-500/20 bg-primary-500/10 px-3 py-1 text-xs font-medium text-primary-500">
                Live sync to markdown
              </span>
              <Tooltip title="Copy current markdown">
                <Button icon={<CopyOutlined />} onClick={() => void handleCopy()}>
                  Copy
                </Button>
              </Tooltip>
            </div>
          </div>

          {activeView === 'outline' && (
            <div className="rounded-2xl border border-border/70 bg-surface-50/90 px-4 py-4 shadow-sm">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-text-secondary">
                <OrderedListOutlined />
                Presentation Title
              </div>
              <Input
                value={outline.presentationTitle}
                onChange={(event) => handlePresentationTitleChange(event.target.value)}
                placeholder="Enter presentation title"
                className="min-h-12 !rounded-xl !border-border/70 !bg-surface-50 !text-xl !font-semibold !text-text-main"
              />
            </div>
          )}
        </div>

        <div className="max-h-[65vh] overflow-y-auto px-5 py-5 sm:px-7">
          {activeView === 'markdown' ? (
            <div className="rounded-[26px] border border-border/70 bg-surface-50 px-5 py-5 shadow-[0_10px_30px_rgba(15,23,42,0.06)]">
              <div className="mb-3 flex items-center justify-between gap-3">
                <span className="text-xs font-semibold uppercase tracking-[0.22em] text-text-secondary">
                  Markdown Source
                </span>
                <span className="text-xs text-text-secondary/70">Raw markdown preview</span>
              </div>
              <div className="rounded-2xl border border-border/70 bg-surface-50 px-6 py-5">
                <pre className="whitespace-pre-wrap break-words font-mono text-[15px] leading-8 text-text-main">
                  {currentMarkdown || '# Empty markdown'}
                </pre>
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              {outline.sections.map((section, index) => (
                <div key={section.id} className="space-y-3">
                  <div
                    className={cn(
                      'overflow-hidden rounded-[26px] border border-border/70 bg-surface-50 shadow-[0_10px_30px_rgba(15,23,42,0.05)]',
                      'transition-all duration-200 hover:border-primary-400/50 hover:shadow-[0_16px_40px_rgba(14,165,233,0.10)]'
                    )}
                  >
                    <div className="flex flex-col border-b border-border/60 bg-surface-100/75 sm:flex-row sm:items-center">
                      <div className="flex items-center gap-4 px-5 py-4 sm:min-w-[220px] sm:border-r sm:border-border/60">
                        <span className="text-3xl font-semibold text-primary-500">{index + 1}</span>
                        <span className="text-base font-semibold text-text-main">Section</span>
                      </div>
                      <div className="flex min-w-0 flex-1 items-center gap-3 px-5 py-4">
                        <Input
                          value={section.title}
                          onChange={(event) =>
                            handleSectionTitleChange(section.id, event.target.value)
                          }
                          placeholder="Section title"
                          className="min-h-11 !rounded-xl !border-border/70 !bg-surface-50 !text-lg !font-semibold !text-text-main"
                        />
                        <Tooltip title="Delete this section">
                          <Button
                            danger
                            type="text"
                            icon={<DeleteOutlined />}
                            onClick={() => handleDeleteSection(section.id)}
                            className="!min-w-11"
                          />
                        </Tooltip>
                      </div>
                    </div>

                    <div className="space-y-3 px-4 py-4 sm:px-5">
                      {section.items.map((item) => (
                        <div
                          key={item.id}
                          className="flex flex-col gap-3 rounded-2xl border border-border/70 bg-surface-100/60 px-4 py-3 sm:flex-row sm:items-center"
                        >
                          <button
                            type="button"
                            onClick={() => handleItemKindToggle(section.id, item.id)}
                            className={cn(
                              'min-h-11 rounded-xl px-3 text-left text-sm font-medium transition-colors',
                              item.kind === 'heading'
                                ? 'bg-primary-500/12 text-primary-500 hover:bg-primary-500/18'
                                : 'bg-surface-200 text-text-secondary hover:bg-surface-300'
                            )}
                          >
                            {item.kind === 'heading' ? 'Topic' : 'Bullet'}
                          </button>
                          <Input
                            value={item.text}
                            onChange={(event) =>
                              handleItemTextChange(section.id, item.id, event.target.value)
                            }
                            placeholder="Outline content"
                            className="min-h-11 flex-1 !rounded-xl !border-border/70 !bg-surface-50 !text-base !text-text-main"
                          />
                          <Tooltip title="Delete this item">
                            <Button
                              type="text"
                              danger
                              icon={<DeleteOutlined />}
                              onClick={() => handleDeleteItem(section.id, item.id)}
                              className="!min-w-11"
                            />
                          </Tooltip>
                        </div>
                      ))}

                      <div className="flex flex-wrap gap-2 pt-1">
                        <Button
                          icon={<PlusOutlined />}
                          onClick={() => handleAddItem(section.id, 'heading')}
                        >
                          Add Topic
                        </Button>
                        <Button
                          icon={<PlusOutlined />}
                          onClick={() => handleAddItem(section.id, 'bullet')}
                        >
                          Add Bullet
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-center">
                    <Button
                      icon={<PlusOutlined />}
                      onClick={() => handleAddSection(index)}
                      className="!min-h-11 !rounded-full !border-dashed !border-border/70 !bg-surface-50 !px-5 !text-text-secondary hover:!border-primary-400/60 hover:!text-primary-500"
                    >
                      Insert Section
                    </Button>
                  </div>
                </div>
              ))}

              {outline.sections.length === 0 && (
                <div className="rounded-[26px] border border-dashed border-border/70 bg-surface-100/70 px-6 py-10 text-center">
                  <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-500/12 text-primary-500">
                    <OrderedListOutlined className="text-xl" />
                  </div>
                  <p className="text-lg font-semibold text-text-main">No sections yet</p>
                  <p className="mt-2 text-sm text-text-secondary">
                    Generate markdown first, or create your first section manually.
                  </p>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => handleAddSection()}
                    className="!mt-5 !min-h-11 !rounded-full"
                  >
                    Add First Section
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
