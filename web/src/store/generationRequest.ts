import type {
  GenerateMarkdownRequest,
  Tone,
  Verbosity,
} from '../api/types/slidegen.types';

interface GenerationRequestConfig {
  tone: Tone;
  verbosity: Verbosity;
  webSearchEnabled: boolean;
  slideCount: number;
  language: string;
  template: string;
}

interface GenerationRequestInput {
  content: string;
  userId: string;
  sessionId?: string;
  fileIds?: string[];
}

export const buildGenerationRequest = (
  config: GenerationRequestConfig,
  input: GenerationRequestInput
): GenerateMarkdownRequest => ({
  content: input.content,
  tone: config.tone,
  verbosity: config.verbosity,
  web_search: config.webSearchEnabled,
  n_slides: config.slideCount,
  language: config.language,
  template: config.template,
  files: input.fileIds && input.fileIds.length > 0 ? input.fileIds : null,
  user_id: input.userId,
  session_id: input.sessionId || null,
});
