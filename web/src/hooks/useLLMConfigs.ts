/**
 * React Query hooks for LLM configurations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { llmConfigApi } from '../api/endpoints/llmConfig';
import type {
  LLMConfigCreate,
  LLMConfigUpdate,
  LLMConfigTest,
  LLMModelsFetchRequest,
} from '../api/types/llmConfig.types';
import { message } from 'antd';

export const useLLMConfigs = () => {
  return useQuery({
    queryKey: ['llm-configs'],
    queryFn: () => llmConfigApi.list(),
  });
};

export const useLLMConfig = (id: string) => {
  return useQuery({
    queryKey: ['llm-configs', id],
    queryFn: () => llmConfigApi.get(id),
    enabled: !!id,
  });
};

export const useCreateLLMConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<LLMConfigCreate, 'user_id'>) =>
      llmConfigApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] });
      message.success('LLM configuration created successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to create LLM configuration');
    },
  });
};

export const useUpdateLLMConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: LLMConfigUpdate }) =>
      llmConfigApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] });
      message.success('LLM configuration updated successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to update LLM configuration');
    },
  });
};

export const useDeleteLLMConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => llmConfigApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] });
      message.success('LLM configuration deleted successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to delete LLM configuration');
    },
  });
};

export const useTestLLMConfig = () => {
  return useMutation({
    mutationFn: (data: LLMConfigTest) => llmConfigApi.test(data),
    onSuccess: (result) => {
      if (result.success) {
        message.success(`Test successful! Latency: ${result.latency?.toFixed(2)}s`);
      } else {
        message.error(result.error || 'Test failed');
      }
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to test configuration');
    },
  });
};

export const useSetDefaultLLMConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => llmConfigApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] });
      message.success('Default configuration updated');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to set default configuration');
    },
  });
};

export const useFetchLLMModels = () => {
  return useMutation({
    mutationFn: (data: LLMModelsFetchRequest) => llmConfigApi.fetchModels(data),
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to fetch models');
    },
  });
};

export const useLLMProviders = () => {
  return useQuery({
    queryKey: ['llm-providers'],
    queryFn: () => llmConfigApi.getProviders(),
    staleTime: Infinity, // Providers rarely change
  });
};
