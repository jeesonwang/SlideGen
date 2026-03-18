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
