/**
 * Custom hook for Server-Sent Events (SSE) streaming
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { message } from 'antd';
import type { MarkdownStreamRequestConfig, SSEEvent } from '../api/types/slidegen.types';

interface UseSSEOptions {
  onMessage?: (event: SSEEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: (finalContent: string) => void;
  autoConnect?: boolean;
}

interface UseSSEReturn {
  connect: (request: string | MarkdownStreamRequestConfig) => void;
  disconnect: () => void;
  isConnected: boolean;
  error: Error | null;
}

export const useSSE = (options: UseSSEOptions = {}): UseSSEReturn => {
  const { onMessage, onError, onComplete } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeRequestRef = useRef<string | MarkdownStreamRequestConfig | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;

  // Store callbacks in refs to avoid reconnections when they change
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const onCompleteRef = useRef(onComplete);

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
    onErrorRef.current = onError;
    onCompleteRef.current = onComplete;
  }, [onMessage, onError, onComplete]);

  const disconnect = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsConnected(false);
  }, []);

  const parseSSEChunk = useCallback(
    (chunk: string) => {
      const lines = chunk.split('\n');
      let eventType = 'message';
      const dataLines: string[] = [];

      lines.forEach((line) => {
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim();
          return;
        }

        if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trimStart());
        }
      });

      if (dataLines.length === 0) {
        return;
      }

      try {
        const data = JSON.parse(dataLines.join('\n'));
        const sseEvent: SSEEvent = {
          event: eventType as SSEEvent['event'],
          ...data,
        } as SSEEvent;

        onMessageRef.current?.(sseEvent);

        if (eventType === 'workflow_completed') {
          disconnect();
          onCompleteRef.current?.(data.content || '');
          return;
        }

        if (eventType === 'workflow_error') {
          disconnect();
          const err = new Error(data.error || 'Generation failed');
          setError(err);
          onErrorRef.current?.(err);
          message.error(data.error || 'Generation failed');
        }
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    },
    [disconnect]
  );

  const connect = useCallback(
    (request: string | MarkdownStreamRequestConfig) => {
      disconnect();
      activeRequestRef.current = request;

      const controller = new AbortController();
      abortControllerRef.current = controller;

      const target = typeof request === 'string' ? { url: request, options: { method: 'GET' } } : request;

      void (async () => {
        try {
          const response = await fetch(target.url, {
            ...target.options,
            signal: controller.signal,
          });

          if (!response.ok) {
            throw new Error(`Connection failed (${response.status})`);
          }

          if (!response.body) {
            throw new Error('Streaming is not supported in this browser');
          }

          setIsConnected(true);
          setError(null);
          reconnectAttemptsRef.current = 0;

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { value, done } = await reader.read();
            if (done) {
              break;
            }

            buffer += decoder.decode(value, { stream: true });

            let boundaryIndex = buffer.indexOf('\n\n');
            while (boundaryIndex !== -1) {
              const chunk = buffer.slice(0, boundaryIndex).trim();
              buffer = buffer.slice(boundaryIndex + 2);
              if (chunk) {
                parseSSEChunk(chunk);
              }
              boundaryIndex = buffer.indexOf('\n\n');
            }
          }
        } catch (err) {
          if (controller.signal.aborted) {
            return;
          }

          console.error('SSE Error:', err);
          const streamError = err instanceof Error ? err : new Error('Connection error');
          setError(streamError);
          setIsConnected(false);

          if (reconnectAttemptsRef.current < maxReconnectAttempts && activeRequestRef.current) {
            reconnectAttemptsRef.current++;
            message.warning(
              `Connection lost. Retrying... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
            );
            setTimeout(() => {
              if (activeRequestRef.current) {
                connect(activeRequestRef.current);
              }
            }, 2000 * reconnectAttemptsRef.current);
          } else {
            disconnect();
            message.error('Failed to connect after multiple attempts');
            onErrorRef.current?.(streamError);
          }
        }
      })();
    },
    [disconnect, parseSSEChunk]
  );

  // Auto-connect if URL is provided
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    isConnected,
    error,
  };
};
