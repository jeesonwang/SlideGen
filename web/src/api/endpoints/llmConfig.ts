/**
 * LLM Configuration API endpoints
 */

import apiClient from '../client';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  LLMConfigPublic,
  LLMConfigsPublic,
  LLMConfigCreate,
  LLMConfigUpdate,
  LLMConfigTest,
  LLMConfigTestResult,
  LLMModelsFetchRequest,
  LLMProvidersInfo,
  AvailableModels,
} from '../types/llmConfig.types';
import type { Message } from '../types/common.types';

export const llmConfigApi = {
  /**
   * Get all LLM configurations for the current user
   */
  list: async (): Promise<LLMConfigsPublic> => {
    const response = await apiClient.get<LLMConfigsPublic>(
      API_ENDPOINTS.LLM_CONFIG.LIST
    );
    return response.data;
  },

  /**
   * Get a single LLM configuration by ID
   */
  get: async (id: string): Promise<LLMConfigPublic> => {
    const response = await apiClient.get<LLMConfigPublic>(
      API_ENDPOINTS.LLM_CONFIG.GET(id)
    );
    return response.data;
  },

  /**
   * Create a new LLM configuration
   */
  create: async (data: Omit<LLMConfigCreate, 'user_id'>): Promise<LLMConfigPublic> => {
    const response = await apiClient.post<LLMConfigPublic>(
      API_ENDPOINTS.LLM_CONFIG.CREATE,
      data
    );
    return response.data;
  },

  /**
   * Update an existing LLM configuration
   */
  update: async (id: string, data: LLMConfigUpdate): Promise<LLMConfigPublic> => {
    const response = await apiClient.patch<LLMConfigPublic>(
      API_ENDPOINTS.LLM_CONFIG.UPDATE(id),
      data
    );
    return response.data;
  },

  /**
   * Delete an LLM configuration
   */
  delete: async (id: string): Promise<Message> => {
    const response = await apiClient.delete<Message>(
      API_ENDPOINTS.LLM_CONFIG.DELETE(id)
    );
    return response.data;
  },

  /**
   * Test an LLM configuration
   */
  test: async (data: LLMConfigTest): Promise<LLMConfigTestResult> => {
    const response = await apiClient.post<LLMConfigTestResult>(
      API_ENDPOINTS.LLM_CONFIG.TEST,
      data
    );
    return response.data;
  },

  /**
   * Fetch available models from the current provider configuration
   */
  fetchModels: async (data: LLMModelsFetchRequest): Promise<AvailableModels> => {
    const response = await apiClient.post<AvailableModels>(
      API_ENDPOINTS.LLM_CONFIG.FETCH_MODELS,
      data
    );
    return response.data;
  },

  /**
   * Set an LLM configuration as default
   */
  setDefault: async (id: string): Promise<LLMConfigPublic> => {
    const response = await apiClient.post<LLMConfigPublic>(
      API_ENDPOINTS.LLM_CONFIG.SET_DEFAULT(id)
    );
    return response.data;
  },

  /**
   * Get all available LLM providers
   */
  getProviders: async (): Promise<LLMProvidersInfo> => {
    const response = await apiClient.get<LLMProvidersInfo>(
      API_ENDPOINTS.LLM_CONFIG.PROVIDERS
    );
    return response.data;
  },
};
