/**
 * SlideGen API endpoints for PPT generation
 */

import apiClient from '../client';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  GenerateMarkdownRequest,
  MarkdownToPPTRequest,
  GeneratePPTXResponse,
} from '../types/slidegen.types';

export const slidegenApi = {
  /**
   * Generate markdown content with SSE streaming
   * Note: This returns the URL for SSE connection, not the actual request
   */
  getMarkdownStreamURL: (params: GenerateMarkdownRequest): string => {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:7860';
    const url = new URL(
      API_ENDPOINTS.SLIDEGEN.GENERATE_MARKDOWN_STREAM,
      baseURL
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
