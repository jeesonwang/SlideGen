import { message } from 'antd';
import { chatMessagesApi } from '../../api/endpoints/chatMessages';
import type { MarkdownStreamRequestConfig, SSEEvent } from '../../api/types/slidegen.types';
import { useSSE } from '../../hooks/useSSE';
import { getAssistantMessageContent } from './chatLogic';

interface UsePresentationStreamOptions {
  currentSessionId: string | null;
  streamingContent: string;
  appendStreamChunk: (chunk: string) => void;
  finalizeStreamingMessage: (finalContent?: string) => void;
  setStreaming: (isStreaming: boolean) => void;
  setMarkdownContent: (content: string) => void;
  setStep: (step: 'editing') => void;
  onStreamError: () => void;
}

export const usePresentationStream = ({
  currentSessionId,
  streamingContent,
  appendStreamChunk,
  finalizeStreamingMessage,
  setStreaming,
  setMarkdownContent,
  setStep,
  onStreamError,
}: UsePresentationStreamOptions) => {
  const { connect } = useSSE({
    onMessage: (event: SSEEvent) => {
      if (event.event === 'content_generated' && 'content' in event) {
        appendStreamChunk(event.content);
      }
      if (event.event === 'step_completed' && 'content' in event && event.content) {
        appendStreamChunk(event.content);
      }
      if (event.event === 'loop_iteration_completed' && 'content' in event && event.content) {
        appendStreamChunk(`\n\n${event.content}`);
      }
    },
    onComplete: async (finalContent: string) => {
      const assistantContent = getAssistantMessageContent({
        finalContent,
        streamingContent,
      });

      finalizeStreamingMessage(assistantContent);
      setMarkdownContent(assistantContent);
      setStep('editing');

      if (currentSessionId && assistantContent) {
        try {
          await chatMessagesApi.addMessage(currentSessionId, {
            session_id: currentSessionId,
            role: 'assistant',
            content: assistantContent,
          });
        } catch (saveError) {
          console.error('Failed to save assistant message:', saveError);
        }
      }
    },
    onError: (streamError) => {
      onStreamError();
      setStreaming(false);
      message.error(streamError.message || 'Generation failed. Please try again.');
    },
  });

  return {
    startPresentationStream: (request: string | MarkdownStreamRequestConfig) => connect(request),
  };
};
