/**
 * File management API endpoints
 */

import apiClient from '../client';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  FileMetadatasPublic,
  FileUploadResponse,
} from '../types/file.types';
import type { Message } from '../types/common.types';

export const filesApi = {
  /**
   * Upload a single file
   */
  upload: async (
    file: File,
    sessionId: string
  ): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    const response = await apiClient.post<FileUploadResponse>(
      API_ENDPOINTS.FILES.UPLOAD,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Upload multiple files
   */
  uploadMultiple: async (
    files: File[],
    sessionId: string
  ): Promise<FileUploadResponse[]> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('session_id', sessionId);

    const response = await apiClient.post<FileUploadResponse[]>(
      API_ENDPOINTS.FILES.UPLOAD_MULTIPLE,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Get all files for the current user
   */
  list: async (params?: {
    skip?: number;
    limit?: number;
    session_id?: string;
  }): Promise<FileMetadatasPublic> => {
    const response = await apiClient.get<FileMetadatasPublic>(
      API_ENDPOINTS.FILES.LIST,
      { params }
    );
    return response.data;
  },

  /**
   * Delete a file
   */
  delete: async (id: string): Promise<Message> => {
    const response = await apiClient.delete<Message>(
      API_ENDPOINTS.FILES.DELETE(id)
    );
    return response.data;
  },

  /**
   * Download a file
   */
  download: async (id: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(
      API_ENDPOINTS.FILES.DOWNLOAD(id),
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },
};
