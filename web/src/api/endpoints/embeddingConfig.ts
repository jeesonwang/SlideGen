/**
 * Embedding Configuration API endpoints
 */

import apiClient from '../client';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  EmbeddingConfigPublic,
  EmbeddingConfigsPublic,
  EmbeddingConfigCreate,
  EmbeddingConfigUpdate,
  EmbeddingConfigTest,
  EmbeddingConfigTestResult,
  EmbeddingProvidersInfo,
  AvailableEmbeddingModels,
} from '../types/embeddingConfig.types';
import type { Message } from '../types/common.types';

export const embeddingConfigApi = {
  /**
   * Get all Embedding configurations for the current user
   */
  list: async (): Promise<EmbeddingConfigsPublic> => {
    const response = await apiClient.get<EmbeddingConfigsPublic>(
      API_ENDPOINTS.EMBEDDING_CONFIG.LIST
    );
    return response.data;
  },

  /**
   * Get a single Embedding configuration by ID
   */
  get: async (id: string): Promise<EmbeddingConfigPublic> => {
    const response = await apiClient.get<EmbeddingConfigPublic>(
      API_ENDPOINTS.EMBEDDING_CONFIG.GET(id)
    );
    return response.data;
  },

  /**
   * Create a new Embedding configuration
   */
  create: async (
    data: Omit<EmbeddingConfigCreate, 'user_id'>
  ): Promise<EmbeddingConfigPublic> => {
    const response = await apiClient.post<EmbeddingConfigPublic>(
      API_ENDPOINTS.EMBEDDING_CONFIG.CREATE,
      data
    );
    return response.data;
  },

  /**
   * Update an existing Embedding configuration
   */
  update: async (
    id: string,
    data: EmbeddingConfigUpdate
  ): Promise<EmbeddingConfigPublic> => {
    const response = await apiClient.patch<EmbeddingConfigPublic>(
      API_ENDPOINTS.EMBEDDING_CONFIG.UPDATE(id),
      data
    );
    return response.data;
  },

  /**
   * Delete an Embedding configuration
   */
  delete: async (id: string): Promise<Message> => {
    const response = await apiClient.delete<Message>(
      API_ENDPOINTS.EMBEDDING_CONFIG.DELETE(id)
    );
    return response.data;
  },

  /**
   * Test an Embedding configuration
   */
  test: async (data: EmbeddingConfigTest): Promise<EmbeddingConfigTestResult> => {
    const response = await apiClient.post<EmbeddingConfigTestResult>(
      API_ENDPOINTS.EMBEDDING_CONFIG.TEST,
      data
    );
    return response.data;
  },

  /**
   * Set an Embedding configuration as default
   */
  setDefault: async (id: string): Promise<EmbeddingConfigPublic> => {
    const response = await apiClient.post<EmbeddingConfigPublic>(
      API_ENDPOINTS.EMBEDDING_CONFIG.SET_DEFAULT(id)
    );
    return response.data;
  },

  /**
   * Get all available Embedding providers
   */
  getProviders: async (): Promise<EmbeddingProvidersInfo> => {
    const response = await apiClient.get<EmbeddingProvidersInfo>(
      API_ENDPOINTS.EMBEDDING_CONFIG.PROVIDERS
    );
    return response.data;
  },

  /**
   * Get available models for a provider
   */
  getModels: async (provider: string): Promise<AvailableEmbeddingModels> => {
    const response = await apiClient.get<AvailableEmbeddingModels>(
      API_ENDPOINTS.EMBEDDING_CONFIG.MODELS(provider)
    );
    return response.data;
  },
};
