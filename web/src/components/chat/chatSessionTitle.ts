import { DEFAULT_PRESENTATION_TITLE } from '../../utils/constants.ts';

const MAX_FALLBACK_TITLE_LENGTH = 72;

const normalizeWhitespace = (value?: string | null) =>
  value?.replace(/\s+/g, ' ').trim() || '';

const isPlaceholderSessionTitle = (value: string) => {
  if (!value) {
    return true;
  }

  if (value === DEFAULT_PRESENTATION_TITLE) {
    return true;
  }

  return /^(section|slide|topic)\s+\d+$/i.test(value);
};

const getFallbackTitle = (value?: string | null) => {
  const normalizedValue = normalizeWhitespace(value);
  if (!normalizedValue) {
    return '';
  }

  if (normalizedValue.length <= MAX_FALLBACK_TITLE_LENGTH) {
    return normalizedValue;
  }

  return `${normalizedValue.slice(0, MAX_FALLBACK_TITLE_LENGTH - 1).trimEnd()}…`;
};

export const getSessionDisplayTitle = (
  sessionTitle?: string | null,
  topic?: string | null,
  fallbackContent?: string | null
) => {
  const normalizedTitle = normalizeWhitespace(sessionTitle);
  if (!isPlaceholderSessionTitle(normalizedTitle)) {
    return normalizedTitle;
  }

  return getFallbackTitle(topic) || getFallbackTitle(fallbackContent) || DEFAULT_PRESENTATION_TITLE;
};

export const getChatHeaderTitle = (
  sessionTitle?: string | null,
  topic?: string | null,
  fallbackContent?: string | null
) => {
  return getSessionDisplayTitle(sessionTitle, topic, fallbackContent);
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
