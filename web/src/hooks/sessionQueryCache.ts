import type { QueryClient } from '@tanstack/react-query';
import type {
  SessionPublic,
  SessionsPublic,
  SessionUpdate,
} from '../api/types/session.types';

const isSessionsPublic = (value: unknown): value is SessionsPublic => {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'data' in value &&
      Array.isArray((value as { data?: unknown }).data)
  );
};

export const syncUpdatedSessionInCache = (
  queryClient: QueryClient,
  updatedSession: SessionPublic
) => {
  queryClient.setQueryData(['sessions', updatedSession.id], updatedSession);

  queryClient.setQueriesData({ queryKey: ['sessions'] }, (cachedValue: unknown) => {
    if (!isSessionsPublic(cachedValue)) {
      return cachedValue;
    }

    return {
      ...cachedValue,
      data: cachedValue.data.map((session) =>
        session.id === updatedSession.id ? updatedSession : session
      ),
    };
  });
};

export const mergeSessionWithUpdate = (
  session: SessionPublic,
  update: SessionUpdate
): SessionPublic => {
  const mergedSession = { ...session };

  if (typeof update.title === 'string' && update.title.trim()) {
    mergedSession.title = update.title;
  }

  if (typeof update.status === 'string') {
    mergedSession.status = update.status;
  }

  if (typeof update.topic === 'string' && update.topic.trim()) {
    mergedSession.topic = update.topic;
  }

  if (update.extra_data !== undefined && update.extra_data !== null) {
    mergedSession.extra_data = update.extra_data;
  }

  return mergedSession;
};
