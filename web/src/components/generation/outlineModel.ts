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

export const parseMarkdownToOutline = (markdown: string): OutlineDocument => {
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

  return {
    presentationTitle,
    sections,
  };
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
