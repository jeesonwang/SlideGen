import type { JsonObject } from './common.types';

/**
 * Chat message types for session conversations
 */

export const MessageRole = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
} as const;

export type MessageRole = (typeof MessageRole)[keyof typeof MessageRole];

// Base properties shared across types
export interface ChatMessageBase {
  role: MessageRole;
  content: string;
  extra_data?: JsonObject | null;
}

// Properties for creating a new message
export interface ChatMessageCreate extends ChatMessageBase {
  session_id: string;
}

// Properties returned from API
export interface ChatMessagePublic extends ChatMessageBase {
  id: string;
  session_id: string;
  user_id: string;
  create_time: string;
}

// List response with pagination
export interface ChatMessagesPublic {
  data: ChatMessagePublic[];
  count: number;
}

// Parameters for listing messages
export interface ListMessagesParams {
  skip?: number;
  limit?: number;
}
