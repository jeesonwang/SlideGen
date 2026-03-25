/**
 * React Query hooks for sessions
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionsApi } from '../api/endpoints/sessions';
import type {
  SessionCreate,
  SessionUpdate,
} from '../api/types/session.types';
import { message } from 'antd';

export const useSessions = (params?: {
  skip?: number;
  limit?: number;
  status?: string;
}) => {
  return useQuery({
    queryKey: ['sessions', params],
    queryFn: () => sessionsApi.list(params),
  });
};

export const useSession = (id: string) => {
  return useQuery({
    queryKey: ['sessions', id],
    queryFn: () => sessionsApi.get(id),
    enabled: !!id,
  });
};

export const useCreateSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SessionCreate) => sessionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      message.success('Session created successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to create session');
    },
  });
};

export const useUpdateSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SessionUpdate }) =>
      sessionsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      message.success('Session updated successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to update session');
    },
  });
};

export const useDeleteSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sessionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      message.success('Session deleted successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to delete session');
    },
  });
};
