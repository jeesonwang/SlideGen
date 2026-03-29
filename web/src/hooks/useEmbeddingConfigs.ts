/**
 * React Query hooks for Embedding configurations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { embeddingConfigApi } from '../api/endpoints/embeddingConfig';
import type {
  EmbeddingConfigCreate,
  EmbeddingConfigUpdate,
  EmbeddingConfigTest,
  EmbeddingModelsFetchRequest,
} from '../api/types/embeddingConfig.types';
import { message } from 'antd';
import { getErrorDetail } from '../utils/errorDetail';

export const useEmbeddingConfigs = () => {
  return useQuery({
    queryKey: ['embedding-configs'],
    queryFn: () => embeddingConfigApi.list(),
  });
};

export const useEmbeddingConfig = (id: string) => {
  return useQuery({
    queryKey: ['embedding-configs', id],
    queryFn: () => embeddingConfigApi.get(id),
    enabled: !!id,
  });
};

export const useCreateEmbeddingConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<EmbeddingConfigCreate, 'user_id'>) =>
      embeddingConfigApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['embedding-configs'] });
      message.success('Embedding configuration created successfully');
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to create Embedding configuration'));
    },
  });
};

export const useUpdateEmbeddingConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: EmbeddingConfigUpdate }) =>
      embeddingConfigApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['embedding-configs'] });
      message.success('Embedding configuration updated successfully');
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to update Embedding configuration'));
    },
  });
};

export const useDeleteEmbeddingConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => embeddingConfigApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['embedding-configs'] });
      message.success('Embedding configuration deleted successfully');
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to delete Embedding configuration'));
    },
  });
};

export const useTestEmbeddingConfig = () => {
  return useMutation({
    mutationFn: (data: EmbeddingConfigTest) => embeddingConfigApi.test(data),
    onSuccess: (result) => {
      if (result.success) {
        message.success(
          `Test successful! Dimension: ${result.embedding_dimension}, Latency: ${result.latency?.toFixed(2)}s`
        );
      } else {
        message.error(result.error || 'Test failed');
      }
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to test configuration'));
    },
  });
};

export const useSetDefaultEmbeddingConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => embeddingConfigApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['embedding-configs'] });
      message.success('Default configuration updated');
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to set default configuration'));
    },
  });
};

export const useFetchEmbeddingModels = () => {
  return useMutation({
    mutationFn: (data: EmbeddingModelsFetchRequest) => embeddingConfigApi.fetchModels(data),
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to fetch models'));
    },
  });
};

export const useEmbeddingProviders = () => {
  return useQuery({
    queryKey: ['embedding-providers'],
    queryFn: () => embeddingConfigApi.getProviders(),
    staleTime: Infinity, // Providers rarely change
  });
};
