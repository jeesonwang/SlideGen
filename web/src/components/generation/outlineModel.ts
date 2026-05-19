export type OutlineItemKind = 'heading' | 'bullet';

export interface OutlineTopic {
  id: string;
  kind: OutlineItemKind;
  text: string;
}

export type OutlineItem = OutlineTopic;

export interface OutlineSection {
  id: string;
  kind: 'section';
  title: string;
  items: OutlineTopic[];
}

export interface OutlineChapter {
  id: string;
  kind: 'chapter';
  title: string;
  sections: OutlineSection[];
}

export interface OutlineDocument {
  presentationTitle: string;
  chapters: OutlineChapter[];
}

type ParsedOutlineSection = OutlineSection & {
  sourceLevel: 2 | 3;
};

type ParsedOutlineChapter = Omit<OutlineChapter, 'sections'> & {
  sections: ParsedOutlineSection[];
};

const createIdFactory = () => {
  let chapterIndex = 0;
  let sectionIndex = 0;
  let itemIndex = 0;

  return {
    nextChapterId: () => `chapter-${++chapterIndex}`,
    nextSectionId: () => `section-${++sectionIndex}`,
    nextItemId: () => `item-${++itemIndex}`,
  };
};

const normalizeLine = (line: string) => line.replace(/\r/g, '').trim();
const normalizeIdentityText = (text: string) => text.trim().replace(/\s+/g, ' ').toLowerCase();

const getTopicSignature = (item: OutlineTopic) =>
  `${item.kind}:${normalizeIdentityText(item.text)}`;

const getSectionSignature = (section: OutlineSection) =>
  [
    normalizeIdentityText(section.title),
    ...section.items.map((item) => getTopicSignature(item)),
  ].join('|');

const getChapterSignature = (chapter: OutlineChapter) =>
  [
    normalizeIdentityText(chapter.title),
    ...chapter.sections.map((section) => getSectionSignature(section)),
  ].join('|');

const findReusableIndex = <T>(
  candidates: T[],
  usedIndexes: Set<number>,
  predicate: (candidate: T, index: number) => boolean
) =>
  candidates.findIndex(
    (candidate, index) => !usedIndexes.has(index) && predicate(candidate, index)
  );

const reconcileTopicIds = (
  parsedItems: OutlineTopic[],
  previousItems: OutlineTopic[] = []
): OutlineTopic[] => {
  const usedPreviousIndexes = new Set<number>();

  return parsedItems.map((item, index) => {
    const exactMatchIndex = findReusableIndex(
      previousItems,
      usedPreviousIndexes,
      (previousItem) => getTopicSignature(previousItem) === getTopicSignature(item)
    );
    const positionalKindMatchIndex =
      exactMatchIndex >= 0
        ? exactMatchIndex
        : findReusableIndex(
            previousItems,
            usedPreviousIndexes,
            (previousItem, previousIndex) =>
              previousIndex === index && previousItem.kind === item.kind
          );
    const positionalMatchIndex =
      positionalKindMatchIndex >= 0
        ? positionalKindMatchIndex
        : findReusableIndex(
            previousItems,
            usedPreviousIndexes,
            (_previousItem, previousIndex) => previousIndex === index
          );

    if (positionalMatchIndex < 0) {
      return item;
    }

    usedPreviousIndexes.add(positionalMatchIndex);
    return {
      ...item,
      id: previousItems[positionalMatchIndex].id,
    };
  });
};

const reconcileSectionIds = (
  parsedSections: OutlineSection[],
  previousSections: OutlineSection[] = []
): OutlineSection[] => {
  const usedPreviousIndexes = new Set<number>();

  return parsedSections.map((section, index) => {
    const exactMatchIndex = findReusableIndex(
      previousSections,
      usedPreviousIndexes,
      (previousSection) =>
        getSectionSignature(previousSection) === getSectionSignature(section)
    );
    const titleMatchIndex =
      exactMatchIndex >= 0
        ? exactMatchIndex
        : findReusableIndex(
            previousSections,
            usedPreviousIndexes,
            (previousSection) =>
              normalizeIdentityText(previousSection.title) ===
              normalizeIdentityText(section.title)
          );
    const positionalMatchIndex =
      titleMatchIndex >= 0
        ? titleMatchIndex
        : findReusableIndex(
            previousSections,
            usedPreviousIndexes,
            (_previousSection, previousIndex) => previousIndex === index
          );

    if (positionalMatchIndex < 0) {
      return section;
    }

    const previousSection = previousSections[positionalMatchIndex];
    usedPreviousIndexes.add(positionalMatchIndex);

    return {
      ...section,
      id: previousSection.id,
      items: reconcileTopicIds(section.items, previousSection.items),
    };
  });
};

const reconcileOutlineIds = (
  parsedOutline: OutlineDocument,
  previousOutline?: OutlineDocument | null
): OutlineDocument => {
  if (!previousOutline) {
    return parsedOutline;
  }

  const usedPreviousChapterIndexes = new Set<number>();

  return {
    ...parsedOutline,
    chapters: parsedOutline.chapters.map((chapter, index) => {
      const exactMatchIndex = findReusableIndex(
        previousOutline.chapters,
        usedPreviousChapterIndexes,
        (previousChapter) =>
          getChapterSignature(previousChapter) === getChapterSignature(chapter)
      );
      const titleMatchIndex =
        exactMatchIndex >= 0
          ? exactMatchIndex
          : findReusableIndex(
              previousOutline.chapters,
              usedPreviousChapterIndexes,
              (previousChapter) =>
                normalizeIdentityText(previousChapter.title) ===
                normalizeIdentityText(chapter.title)
            );
      const positionalMatchIndex =
        titleMatchIndex >= 0
          ? titleMatchIndex
          : findReusableIndex(
              previousOutline.chapters,
              usedPreviousChapterIndexes,
              (_previousChapter, previousIndex) => previousIndex === index
            );

      if (positionalMatchIndex < 0) {
        return chapter;
      }

      const previousChapter = previousOutline.chapters[positionalMatchIndex];
      usedPreviousChapterIndexes.add(positionalMatchIndex);

      return {
        ...chapter,
        id: previousChapter.id,
        sections: reconcileSectionIds(chapter.sections, previousChapter.sections),
      };
    }),
  };
};

const createParsedChapter = (
  ids: ReturnType<typeof createIdFactory>,
  title: string
): ParsedOutlineChapter => ({
  id: ids.nextChapterId(),
  kind: 'chapter',
  title,
  sections: [],
});

const createParsedSection = (
  ids: ReturnType<typeof createIdFactory>,
  title: string,
  sourceLevel: 2 | 3
): ParsedOutlineSection => ({
  id: ids.nextSectionId(),
  kind: 'section',
  title,
  items: [],
  sourceLevel,
});

const ensureImplicitSection = (
  ids: ReturnType<typeof createIdFactory>,
  chapter: ParsedOutlineChapter | null
) => {
  if (!chapter) {
    return null;
  }

  const existing = chapter.sections.find((section) => section.sourceLevel === 2);
  if (existing) {
    return existing;
  }

  const section = createParsedSection(ids, chapter.title, 2);
  chapter.sections.push(section);
  return section;
};

const pushLooseTextAsBullet = (
  section: ParsedOutlineSection | null,
  nextItemId: () => string,
  text: string
) => {
  const normalized = text.trim();
  if (!section || !normalized) {
    return;
  }

  section.items.push({
    id: nextItemId(),
    kind: 'bullet',
    text: normalized,
  });
};

const normalizeLegacyChapter = (
  chapter: ParsedOutlineChapter,
  ids: ReturnType<typeof createIdFactory>
): ParsedOutlineChapter => {
  const hasSectionLevelTopics = chapter.sections.some((section) =>
    section.items.some((item) => item.kind === 'heading')
  );
  const hasH3Sections = chapter.sections.some((section) => section.sourceLevel === 3);

  if (hasSectionLevelTopics || !hasH3Sections) {
    return chapter;
  }

  const legacySection = createParsedSection(ids, chapter.title, 2);
  chapter.sections.forEach((section) => {
    if (section.sourceLevel === 3 && section.title.trim()) {
      legacySection.items.push({
        id: ids.nextItemId(),
        kind: 'heading',
        text: section.title.trim(),
      });
    }
    legacySection.items.push(...section.items);
  });

  return {
    ...chapter,
    sections: [legacySection],
  };
};

const stripParsedChapter = (chapter: ParsedOutlineChapter): OutlineChapter => ({
  id: chapter.id,
  kind: 'chapter',
  title: chapter.title,
  sections: chapter.sections.map((section) => ({
    id: section.id,
    kind: 'section',
    title: section.title,
    items: section.items,
  })),
});

export const parseMarkdownToOutline = (
  markdown: string,
  previousOutline?: OutlineDocument | null
): OutlineDocument => {
  const lines = markdown.split('\n');
  const ids = createIdFactory();
  const chapters: ParsedOutlineChapter[] = [];
  let presentationTitle = '';
  let currentChapter: ParsedOutlineChapter | null = null;
  let currentSection: ParsedOutlineSection | null = null;
  let paragraphLines: string[] = [];

  const flushParagraph = () => {
    if (paragraphLines.length === 0) {
      return;
    }

    pushLooseTextAsBullet(
      currentSection,
      ids.nextItemId,
      paragraphLines.join(' ')
    );
    paragraphLines = [];
  };

  lines.forEach((line) => {
    const trimmed = normalizeLine(line);

    if (!trimmed) {
      flushParagraph();
      return;
    }

    if (trimmed.startsWith('# ') && !trimmed.startsWith('## ')) {
      flushParagraph();
      presentationTitle = trimmed.replace(/^#\s+/, '').trim();
      return;
    }

    if (trimmed.startsWith('## ') && !trimmed.startsWith('### ')) {
      flushParagraph();
      currentChapter = createParsedChapter(
        ids,
        trimmed.replace(/^##\s+/, '').trim()
      );
      chapters.push(currentChapter);
      currentSection = null;
      return;
    }

    if (!currentChapter) {
      return;
    }

    if (trimmed.startsWith('### ') && !trimmed.startsWith('#### ')) {
      flushParagraph();
      currentSection = createParsedSection(
        ids,
        trimmed.replace(/^###\s+/, '').trim(),
        3
      );
      currentChapter.sections.push(currentSection);
      return;
    }

    if (trimmed.startsWith('#### ')) {
      flushParagraph();
      currentSection = currentSection ?? ensureImplicitSection(ids, currentChapter);
      currentSection?.items.push({
        id: ids.nextItemId(),
        kind: 'heading',
        text: trimmed.replace(/^####\s+/, '').trim(),
      });
      return;
    }

    currentSection = currentSection ?? ensureImplicitSection(ids, currentChapter);

    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      flushParagraph();
      currentSection?.items.push({
        id: ids.nextItemId(),
        kind: 'bullet',
        text: trimmed.replace(/^[-*]\s+/, '').trim(),
      });
      return;
    }

    paragraphLines.push(trimmed);
  });

  flushParagraph();

  const outline = {
    presentationTitle,
    chapters: chapters
      .map((chapter) => normalizeLegacyChapter(chapter, ids))
      .map(stripParsedChapter),
  };

  return reconcileOutlineIds(outline, previousOutline);
};

export const serializeOutlineToMarkdown = (outline: OutlineDocument): string => {
  const parts: string[] = [];

  if (outline.presentationTitle.trim()) {
    parts.push(`# ${outline.presentationTitle.trim()}`);
  }

  outline.chapters.forEach((chapter) => {
    const chapterTitle = chapter.title.trim();
    if (!chapterTitle) {
      return;
    }

    const sectionBlocks: string[] = [];

    chapter.sections.forEach((section) => {
      const sectionTitle = section.title.trim();
      if (!sectionTitle) {
        return;
      }

      const sectionLines = [`### ${sectionTitle}`];

      section.items.forEach((item, index) => {
        const text = item.text.trim();
        if (!text) {
          return;
        }

        if (item.kind === 'heading') {
          sectionLines.push(`#### ${text}`);
          return;
        }

        const previousItem = section.items[index - 1];
        if (previousItem?.kind === 'bullet') {
          sectionLines.push('');
        }
        sectionLines.push(text);
      });

      sectionBlocks.push(sectionLines.join('\n'));
    });

    if (sectionBlocks.length === 0) {
      parts.push(`## ${chapterTitle}`);
      return;
    }

    parts.push(`## ${chapterTitle}\n${sectionBlocks.join('\n\n')}`);
  });

  return parts.join('\n\n').trim();
};
