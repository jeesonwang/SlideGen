/**
 * Chat store for managing chat session state using Zustand
 */

import { create } from 'zustand';
import { chatMessagesApi } from '../api/endpoints/chatMessages';
import type { ChatMessagePublic, MessageRole } from '../api/types/chatMessage.types';

const getErrorDetail = (error: unknown, fallback: string): string => {
  if (
    error &&
    typeof error === 'object' &&
    'detail' in error &&
    typeof error.detail === 'string'
  ) {
    return error.detail;
  }

  return fallback;
};

interface ChatState {
  // Session
  currentSessionId: string | null;
  
  // Messages
  messages: ChatMessagePublic[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;

  // Actions
  setCurrentSession: (sessionId: string | null) => void;
  loadMessages: (sessionId: string) => Promise<void>;
  addLocalMessage: (role: MessageRole, content: string) => void;
  sendMessage: (content: string) => Promise<ChatMessagePublic | null>;
  appendStreamChunk: (chunk: string) => void;
  finalizeStreamingMessage: (finalContent?: string) => void;
  setStreaming: (isStreaming: boolean) => void;
  resetChat: () => void;
  clearError: () => void;
}

const initialState = {
  currentSessionId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  error: null,
};

export const useChatStore = create<ChatState>((set, get) => ({
  ...initialState,

  setCurrentSession: (sessionId: string | null) => {
    set({ currentSessionId: sessionId, messages: [], error: null });
  },

  loadMessages: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await chatMessagesApi.listMessages(sessionId, { limit: 100 });
      set({ 
        messages: response.data, 
        isLoading: false 
      });
    } catch (error: unknown) {
      set({ 
        error: getErrorDetail(error, 'Failed to load messages'),
        isLoading: false 
      });
    }
  },

  addLocalMessage: (role: MessageRole, content: string) => {
    const tempMessage: ChatMessagePublic = {
      id: `temp-${Date.now()}`,
      session_id: get().currentSessionId || '',
      user_id: '',
      role,
      content,
      create_time: new Date().toISOString(),
    };
    set((state) => ({ 
      messages: [...state.messages, tempMessage] 
    }));
  },

  sendMessage: async (content: string) => {
    const { currentSessionId } = get();
    if (!currentSessionId) {
      set({ error: 'No active session' });
      return null;
    }

    // Add user message locally first for immediate feedback
    get().addLocalMessage('user', content);

    try {
      // Persist to backend
      const savedMessage = await chatMessagesApi.addMessage(currentSessionId, {
        session_id: currentSessionId,
        role: 'user',
        content,
      });

      // Replace temp message with saved one
      set((state) => ({
        messages: state.messages.map((msg) =>
          msg.id.startsWith('temp-') && msg.content === content
            ? savedMessage
            : msg
        ),
      }));

      return savedMessage;
    } catch (error: unknown) {
      set({ error: getErrorDetail(error, 'Failed to send message') });
      return null;
    }
  },

  appendStreamChunk: (chunk: string) => {
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
    }));
  },

  finalizeStreamingMessage: (finalContent?: string) => {
    const { streamingContent, currentSessionId } = get();
    const content = finalContent?.trim() || streamingContent;

    if (content && currentSessionId) {
      // Add the complete streamed message to the messages array
      const assistantMessage: ChatMessagePublic = {
        id: `assistant-${Date.now()}`,
        session_id: currentSessionId,
        user_id: '',
        role: 'assistant',
        content,
        create_time: new Date().toISOString(),
      };
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        streamingContent: '',
        isStreaming: false,
      }));
    }
  },

  setStreaming: (isStreaming: boolean) => {
    set({ isStreaming, streamingContent: isStreaming ? '' : get().streamingContent });
  },

  resetChat: () => {
    set({ ...initialState, currentSessionId: get().currentSessionId });
  },

  clearError: () => {
    set({ error: null });
  },
}));
