/**
 * SlideGen API endpoints for PPT generation
 */

import apiClient from '../client';
import { buildApiUrl } from '../baseUrl';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  GenerateMarkdownRequest,
  MarkdownToPPTRequest,
  GeneratePPTXResponse,
  Template,
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
   * Generate markdown content with SSE streaming
   * Note: This returns the URL for SSE connection, not the actual request
   */
  getMarkdownStreamURL: (params: GenerateMarkdownRequest): string => {
    const url = new URL(
      buildApiUrl(
        API_ENDPOINTS.SLIDEGEN.GENERATE_MARKDOWN_STREAM,
        import.meta.env.VITE_API_BASE_URL,
        import.meta.env.DEV
      ),
      window.location.origin
    );

    // Add query parameters
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((item) => url.searchParams.append(key, String(item)));
        } else {
          url.searchParams.append(key, String(value));
        }
      }
    });

    return url.toString();
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
   * Download generated PPTX file
   */
  downloadPPTX: async (taskId: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(
      API_ENDPOINTS.SLIDEGEN.DOWNLOAD(taskId),
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },
};
