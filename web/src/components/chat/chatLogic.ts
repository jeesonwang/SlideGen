import MarkdownIt from 'markdown-it';

const markdownParser = new MarkdownIt({
  html: false,
  linkify: false,
  typographer: false,
});

interface AssistantMessageContentOptions {
  finalContent: string;
  streamingContent: string;
}

interface SessionCreationOptions {
  currentSessionId: string | null;
  hasUser: boolean;
  content: string;
}

export const getAssistantMessageContent = ({
  finalContent,
  streamingContent,
}: AssistantMessageContentOptions): string => {
  const normalizedFinalContent = finalContent.trim();
  return normalizedFinalContent || streamingContent;
};

export const shouldCreateSessionForSend = ({
  currentSessionId,
  hasUser,
  content,
}: SessionCreationOptions): boolean => {
  return !currentSessionId && hasUser && content.trim().length > 0;
};

export const isPresentationOutlineMarkdown = (content: string): boolean => {
  const tokens = markdownParser.parse(content, {});
  const firstMeaningfulToken = tokens.find(
    (token) => token.type !== 'softbreak' && token.type !== 'hardbreak'
  );

  if (!firstMeaningfulToken || firstMeaningfulToken.type !== 'heading_open') {
    return false;
  }

  const headings = tokens.filter((token) => token.type === 'heading_open');
  const startsWithTitle = firstMeaningfulToken.tag === 'h1';
  const hasSectionHeading = headings.some((token) => token.tag === 'h2');

  return startsWithTitle && hasSectionHeading;
};
