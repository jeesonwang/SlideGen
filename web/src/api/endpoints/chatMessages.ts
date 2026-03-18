/**
 * Chat messages API endpoints for session conversations
 */

import apiClient from '../client';
import type {
  ChatMessageCreate,
  ChatMessagePublic,
  ChatMessagesPublic,
  ListMessagesParams,
} from '../types/chatMessage.types';
import type { Message } from '../types/common.types';

const BASE_PATH = '/api/v1/sessions';

export const chatMessagesApi = {
  /**
   * Add a new message to a session
   */
  addMessage: async (
    sessionId: string,
    message: ChatMessageCreate
  ): Promise<ChatMessagePublic> => {
    const response = await apiClient.post<ChatMessagePublic>(
      `${BASE_PATH}/${sessionId}/messages`,
      message
    );
    return response.data;
  },

  /**
   * List messages for a session with pagination
   */
  listMessages: async (
    sessionId: string,
    params?: ListMessagesParams
  ): Promise<ChatMessagesPublic> => {
    const response = await apiClient.get<ChatMessagesPublic>(
      `${BASE_PATH}/${sessionId}/messages`,
      { params }
    );
    return response.data;
  },

  /**
   * Get a single message by ID
   */
  getMessage: async (
    sessionId: string,
    messageId: string
  ): Promise<ChatMessagePublic> => {
    const response = await apiClient.get<ChatMessagePublic>(
      `${BASE_PATH}/${sessionId}/messages/${messageId}`
    );
    return response.data;
  },

  /**
   * Delete a message
   */
  deleteMessage: async (
    sessionId: string,
    messageId: string
  ): Promise<Message> => {
    const response = await apiClient.delete<Message>(
      `${BASE_PATH}/${sessionId}/messages/${messageId}`
    );
    return response.data;
  },
};
