export type OutlineItemKind = 'heading' | 'bullet';

export interface OutlineItem {
  id: string;
  kind: OutlineItemKind;
  text: string;
}

export interface OutlineSection {
  id: string;
  kind: 'section';
  title: string;
  items: OutlineItem[];
}

export interface OutlineDocument {
  presentationTitle: string;
  sections: OutlineSection[];
}

const createIdFactory = () => {
  let sectionIndex = 0;
  let itemIndex = 0;

  return {
    nextSectionId: () => `section-${++sectionIndex}`,
    nextItemId: () => `item-${++itemIndex}`,
  };
};

const normalizeLine = (line: string) => line.replace(/\r/g, '').trim();
const normalizeIdentityText = (text: string) => text.trim().replace(/\s+/g, ' ').toLowerCase();

const getSectionSignature = (section: OutlineSection) =>
  [
    normalizeIdentityText(section.title),
    ...section.items.map(
      (item) => `${item.kind}:${normalizeIdentityText(item.text)}`
    ),
  ].join('|');

const getItemSignature = (item: OutlineItem) =>
  `${item.kind}:${normalizeIdentityText(item.text)}`;

const findReusableIndex = <T>(
  candidates: T[],
  usedIndexes: Set<number>,
  predicate: (candidate: T, index: number) => boolean
) =>
  candidates.findIndex(
    (candidate, index) => !usedIndexes.has(index) && predicate(candidate, index)
  );

const reconcileItemIds = (
  parsedItems: OutlineItem[],
  previousItems: OutlineItem[] = []
): OutlineItem[] => {
  const usedPreviousIndexes = new Set<number>();

  return parsedItems.map((item, index) => {
    const exactMatchIndex = findReusableIndex(
      previousItems,
      usedPreviousIndexes,
      (previousItem) => getItemSignature(previousItem) === getItemSignature(item)
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

const reconcileOutlineIds = (
  parsedOutline: OutlineDocument,
  previousOutline?: OutlineDocument | null
): OutlineDocument => {
  if (!previousOutline) {
    return parsedOutline;
  }

  const usedPreviousSectionIndexes = new Set<number>();

  return {
    ...parsedOutline,
    sections: parsedOutline.sections.map((section, index) => {
      const exactMatchIndex = findReusableIndex(
        previousOutline.sections,
        usedPreviousSectionIndexes,
        (previousSection) =>
          getSectionSignature(previousSection) === getSectionSignature(section)
      );
      const titleMatchIndex =
        exactMatchIndex >= 0
          ? exactMatchIndex
          : findReusableIndex(
              previousOutline.sections,
              usedPreviousSectionIndexes,
              (previousSection) =>
                normalizeIdentityText(previousSection.title) ===
                normalizeIdentityText(section.title)
            );
      const positionalMatchIndex =
        titleMatchIndex >= 0
          ? titleMatchIndex
          : findReusableIndex(
              previousOutline.sections,
              usedPreviousSectionIndexes,
              (_previousSection, previousIndex) => previousIndex === index
            );

      if (positionalMatchIndex < 0) {
        return section;
      }

      const previousSection = previousOutline.sections[positionalMatchIndex];
      usedPreviousSectionIndexes.add(positionalMatchIndex);

      return {
        ...section,
        id: previousSection.id,
        items: reconcileItemIds(section.items, previousSection.items),
      };
    }),
  };
};

const pushLooseTextAsBullet = (
  section: OutlineSection | null,
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

export const parseMarkdownToOutline = (
  markdown: string,
  previousOutline?: OutlineDocument | null
): OutlineDocument => {
  const lines = markdown.split('\n');
  const ids = createIdFactory();
  const sections: OutlineSection[] = [];
  let presentationTitle = '';
  let currentSection: OutlineSection | null = null;

  const commitSection = () => {
    if (currentSection) {
      sections.push(currentSection);
    }
  };

  lines.forEach((line) => {
    const trimmed = normalizeLine(line);

    if (!trimmed) {
      return;
    }

    if (trimmed.startsWith('# ') && !trimmed.startsWith('## ')) {
      presentationTitle = trimmed.replace(/^#\s+/, '').trim();
      return;
    }

    if (trimmed.startsWith('## ')) {
      commitSection();
      currentSection = {
        id: ids.nextSectionId(),
        kind: 'section',
        title: trimmed.replace(/^##\s+/, '').trim(),
        items: [],
      };
      return;
    }

    if (!currentSection) {
      return;
    }

    if (trimmed.startsWith('### ')) {
      currentSection.items.push({
        id: ids.nextItemId(),
        kind: 'heading',
        text: trimmed.replace(/^###\s+/, '').trim(),
      });
      return;
    }

    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      currentSection.items.push({
        id: ids.nextItemId(),
        kind: 'bullet',
        text: trimmed.replace(/^[-*]\s+/, '').trim(),
      });
      return;
    }

    pushLooseTextAsBullet(currentSection, ids.nextItemId, trimmed);
  });

  commitSection();

  return reconcileOutlineIds({
    presentationTitle,
    sections,
  }, previousOutline);
};

export const serializeOutlineToMarkdown = (outline: OutlineDocument): string => {
  const parts: string[] = [];

  if (outline.presentationTitle.trim()) {
    parts.push(`# ${outline.presentationTitle.trim()}`);
  }

  outline.sections.forEach((section) => {
    const title = section.title.trim();
    if (!title) {
      return;
    }

    const blockLines = [`## ${title}`];

    section.items.forEach((item) => {
      const text = item.text.trim();
      if (!text) {
        return;
      }

      if (item.kind === 'heading') {
        blockLines.push(`### ${text}`);
        return;
      }

      blockLines.push(`- ${text}`);
    });

    parts.push(blockLines.join('\n'));
  });

  return parts.join('\n\n').trim();
};
