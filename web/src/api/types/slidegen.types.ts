import type { JsonObject } from './common.types';

/**
 * Slidegen types for PPT generation workflow
 */

export const Tone = {
  DEFAULT: 'default',
  CASUAL: 'casual',
  PROFESSIONAL: 'professional',
  FUNNY: 'funny',
  EDUCATIONAL: 'educational',
  SALES_PITCH: 'sales_pitch',
} as const;

export type Tone = (typeof Tone)[keyof typeof Tone];

export const Verbosity = {
  CONCISE: 'concise',
  STANDARD: 'standard',
  TEXT_HEAVY: 'text-heavy',
} as const;

export type Verbosity = (typeof Verbosity)[keyof typeof Verbosity];

export type ExportFormat = 'pptx' | 'pdf';

export interface BaseGenerationRequest {
  content: string;
  instructions?: string | null;
  tone: Tone;
  verbosity: Verbosity;
  web_search: boolean;
  n_slides: number;
  language: string;
  files?: string[] | null;
  user_id: string;
  llm_config_id?: string | null;
  embedding_config_id?: string | null;
  session_id?: string | null;
}

export interface GeneratePresentationRequest extends BaseGenerationRequest {
  slides_markdown?: string[] | null;
  template: string;
  include_table_of_contents: boolean;
  include_title_slide: boolean;
  export_as: ExportFormat;
}

export interface GenerateMarkdownRequest extends BaseGenerationRequest {
  template?: string;
}

export interface MarkdownStreamRequestConfig {
  url: string;
  allowReconnect?: boolean;
  options: {
    method: 'POST';
    headers: {
      'Content-Type': 'application/json';
      Authorization?: string;
    };
    body: string;
  };
}

export interface MarkdownToPPTRequest {
  markdown_content: string;
  template: string;
  export_as: ExportFormat;
  theme_preset?: string | null;
}

// SSE Stream Event Types
export const StreamEventType = {
  WORKFLOW_STARTED: 'workflow_started',
  WORKFLOW_COMPLETED: 'workflow_completed',
  WORKFLOW_ERROR: 'workflow_error',
  GENERATION_COMPLETED: 'generation_completed',
  STEP_STARTED: 'step_started',
  STEP_COMPLETED: 'step_completed',
  STEP_ERROR: 'step_error',
  LOOP_STARTED: 'loop_started',
  LOOP_ITERATION_STARTED: 'loop_iteration_started',
  LOOP_ITERATION_COMPLETED: 'loop_iteration_completed',
  LOOP_COMPLETED: 'loop_completed',
  CONTENT_GENERATED: 'content_generated',
  PROGRESS: 'progress',
} as const;

export type StreamEventType = (typeof StreamEventType)[keyof typeof StreamEventType];

export interface StreamEvent {
  event: StreamEventType;
  data?: JsonObject | null;
  message?: string | null;
}

export interface WorkflowStartedEvent {
  event: 'workflow_started';
  workflow_name?: string | null;
  run_id?: string | null;
  message: string;
}

export interface WorkflowCompletedEvent {
  event: 'workflow_completed';
  content?: string | null;
  message: string;
}

export interface WorkflowErrorEvent {
  event: 'workflow_error';
  error: string;
  message: string;
}

export interface GenerationCompletedEvent {
  event: 'generation_completed';
  output_path: string;
  filename: string;
  download_url: string;
  message: string;
}

export interface StepStartedEvent {
  event: 'step_started';
  step_name: string;
  step_index?: number | null;
  message?: string | null;
}

export interface StepCompletedEvent {
  event: 'step_completed';
  step_name: string;
  step_index?: number | null;
  content?: string | null;
  message?: string | null;
}

export interface StepErrorEvent {
  event: 'step_error';
  step_name: string;
  error: string;
}

export interface LoopProgressEvent {
  event: 'loop_iteration_completed';
  iteration: number;
  total: number;
  section_title?: string | null;
  content?: string | null;
  message?: string | null;
}

export interface ContentGeneratedEvent {
  event: 'content_generated';
  content_type: string;
  content: string;
  message?: string | null;
}

export interface ProgressEvent {
  event: 'progress';
  stage: string;
  progress: number;
  message?: string | null;
}

export type SSEEvent =
  | WorkflowStartedEvent
  | WorkflowCompletedEvent
  | WorkflowErrorEvent
  | GenerationCompletedEvent
  | StepStartedEvent
  | StepCompletedEvent
  | StepErrorEvent
  | LoopProgressEvent
  | ContentGeneratedEvent
  | ProgressEvent;

export interface GeneratePPTXResponse {
  success: boolean;
  result: {
    output_path: string;
    filename: string;
    download_url: string;
  } | null;
  message: string;
  error?: string | null;
}

export interface DownloadPPTXResponse {
  url: string;
  filename: string;
}

export interface Template {
  id: string;
  name: string;
  thumbnail?: string;
}

export interface ThemePreset {
  id: string;
  name: string;
}
