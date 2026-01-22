/**
 * Custom hook for Server-Sent Events (SSE) streaming
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { message } from 'antd';
import type { SSEEvent } from '../api/types/slidegen.types';
import { storage } from '../utils/storage';

interface UseSSEOptions {
  onMessage?: (event: SSEEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: (finalContent: string) => void;
  autoConnect?: boolean;
}

interface UseSSEReturn {
  connect: (url: string) => void;
  disconnect: () => void;
  isConnected: boolean;
  error: Error | null;
}

export const useSSE = (options: UseSSEOptions = {}): UseSSEReturn => {
  const { onMessage, onError, onComplete } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
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
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const connect = useCallback(
    (url: string) => {
      // Disconnect existing connection
      disconnect();

      try {
        // Add token to URL for authentication
        const token = storage.getToken();
        const urlWithAuth = new URL(url);
        if (token) {
          urlWithAuth.searchParams.set('token', token);
        }

        const eventSource = new EventSource(urlWithAuth.toString());
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          setIsConnected(true);
          setError(null);
          reconnectAttemptsRef.current = 0;
        };

        eventSource.onerror = (event) => {
          console.error('SSE Error:', event);
          const err = new Error('Connection error');
          setError(err);
          setIsConnected(false);

          // Retry logic
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            reconnectAttemptsRef.current++;
            message.warning(
              `Connection lost. Retrying... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
            );
            setTimeout(() => {
              connect(url);
            }, 2000 * reconnectAttemptsRef.current);
          } else {
            disconnect();
            message.error('Failed to connect after multiple attempts');
            onErrorRef.current?.(err);
          }
        };

        // Listen for all SSE event types
        const eventTypes = [
          'workflow_started',
          'workflow_completed',
          'workflow_error',
          'step_started',
          'step_completed',
          'step_error',
          'loop_started',
          'loop_iteration_started',
          'loop_iteration_completed',
          'loop_completed',
          'content_generated',
          'progress',
        ];

        eventTypes.forEach((eventType) => {
          eventSource.addEventListener(eventType, (event: MessageEvent) => {
            try {
              const data = JSON.parse(event.data);
              const sseEvent: SSEEvent = {
                event: eventType,
                ...data,
              } as SSEEvent;

              onMessageRef.current?.(sseEvent);

              // Handle completion
              if (eventType === 'workflow_completed') {
                disconnect();
                onCompleteRef.current?.(data.content || '');
              }

              // Handle errors
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
          });
        });
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to connect');
        setError(error);
        onErrorRef.current?.(error);
      }
    },
    [disconnect]
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
