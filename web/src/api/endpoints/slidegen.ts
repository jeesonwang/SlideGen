/**
 * SlideGen API endpoints for PPT generation
 */

import apiClient from '../client';
import { buildApiUrl } from '../baseUrl';
import { API_ENDPOINTS } from '../../utils/constants';
import { useAuthStore } from '../../store/authStore';
import type {
  GenerateMarkdownRequest,
  MarkdownStreamRequestConfig,
  MarkdownToPPTRequest,
  GeneratePPTXResponse,
  Template,
  ThemePreset,
} from '../types/slidegen.types';

export const slidegenApi = {
  /**
   * Get available templates
   */
  getTemplates: async (): Promise<Template[]> => {
    const response = await apiClient.get<Template[]>(
      API_ENDPOINTS.SLIDEGEN.TEMPLATES
    );
    return response.data;
  },

  /**
   * Get available theme presets
   */
  getThemePresets: async (): Promise<ThemePreset[]> => {
    const response = await apiClient.get<{ presets: ThemePreset[] }>(
      API_ENDPOINTS.SLIDEGEN.THEME_PRESETS
    );
    return response.data.presets;
  },
  /**
   * Generate markdown content with SSE streaming
   * Note: This returns the URL for SSE connection, not the actual request
   */
  getMarkdownStreamRequest: (params: GenerateMarkdownRequest): MarkdownStreamRequestConfig => {
    const url = new URL(
      buildApiUrl(
        API_ENDPOINTS.SLIDEGEN.GENERATE_MARKDOWN_STREAM,
        import.meta.env.VITE_API_BASE_URL,
        import.meta.env.DEV
      ),
      window.location.origin
    );

    const payload = Object.fromEntries(
      Object.entries(params).filter(([, value]) => value !== undefined && value !== null)
    );
    const token = useAuthStore.getState().token;

    return {
      url: url.toString(),
      allowReconnect: false,
      options: {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      },
    };
  },

  /**
   * Generate PPTX from markdown content
   */
  generatePPTXFromMarkdown: async (
    data: MarkdownToPPTRequest
  ): Promise<GeneratePPTXResponse> => {
    const response = await apiClient.post<GeneratePPTXResponse>(
      API_ENDPOINTS.SLIDEGEN.GENERATE_PPTX_FROM_MARKDOWN,
      data,
      {
        timeout: 120000, // 2 minutes for PPT generation
      }
    );
    return response.data;
  },

  /**
   * Generate PPTX from markdown content with SSE progress updates.
   */
  getPPTXFromMarkdownStreamRequest: (data: MarkdownToPPTRequest): MarkdownStreamRequestConfig => {
    const url = new URL(
      buildApiUrl(
        API_ENDPOINTS.SLIDEGEN.GENERATE_PPTX_FROM_MARKDOWN_STREAM,
        import.meta.env.VITE_API_BASE_URL,
        import.meta.env.DEV
      ),
      window.location.origin
    );

    const token = useAuthStore.getState().token;

    return {
      url: url.toString(),
      allowReconnect: false,
      options: {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
      },
    };
  },

  /**
   * Download generated PPTX file
   */
  downloadPPTX: async (filename: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(
      API_ENDPOINTS.SLIDEGEN.DOWNLOAD(filename),
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },
};
