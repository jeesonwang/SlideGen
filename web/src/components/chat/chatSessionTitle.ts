const DEFAULT_CHAT_TITLE = 'AI Presentation Assistant';

export const getChatHeaderTitle = (sessionTitle?: string | null) => {
  const normalizedTitle = sessionTitle?.trim();
  return normalizedTitle || DEFAULT_CHAT_TITLE;
};

export const getUpdatedSessionTitle = (
  draftTitle: string,
  currentTitle?: string | null
) => {
  const normalizedDraft = draftTitle.trim();
  const normalizedCurrent = currentTitle?.trim() || '';

  if (!normalizedDraft) {
    return normalizedCurrent;
  }

  return normalizedDraft;
};

export const shouldSubmitTitleChange = (
  draftTitle: string,
  currentTitle?: string | null
) => {
  const nextTitle = getUpdatedSessionTitle(draftTitle, currentTitle);
  return Boolean(nextTitle) && nextTitle !== (currentTitle?.trim() || '');
};
