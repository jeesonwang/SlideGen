/**
 * Session API endpoints
 */

import apiClient from '../client';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  SessionPublic,
  SessionsPublic,
  SessionCreate,
  SessionUpdate,
} from '../types/session.types';
import type { Message } from '../types/common.types';

export const sessionsApi = {
  /**
   * Get all sessions for the current user
   */
  list: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<SessionsPublic> => {
    const response = await apiClient.get<SessionsPublic>(
      API_ENDPOINTS.SESSIONS.LIST,
      { params }
    );
    return response.data;
  },

  /**
   * Get a single session by ID
   */
  get: async (id: string): Promise<SessionPublic> => {
    const response = await apiClient.get<SessionPublic>(
      API_ENDPOINTS.SESSIONS.GET(id)
    );
    return response.data;
  },

  /**
   * Create a new session
   */
  create: async (data: SessionCreate): Promise<SessionPublic> => {
    const response = await apiClient.post<SessionPublic>(
      API_ENDPOINTS.SESSIONS.CREATE,
      data
    );
    return response.data;
  },

  /**
   * Update an existing session
   */
  update: async (id: string, data: SessionUpdate): Promise<SessionPublic> => {
    const response = await apiClient.patch<SessionPublic>(
      API_ENDPOINTS.SESSIONS.UPDATE(id),
      data
    );
    return response.data;
  },

  /**
   * Delete a session
   */
  delete: async (id: string): Promise<Message> => {
    const response = await apiClient.delete<Message>(
      API_ENDPOINTS.SESSIONS.DELETE(id)
    );
    return response.data;
  },

  /**
   * Archive a session
   */
  archive: async (id: string): Promise<SessionPublic> => {
    const response = await apiClient.post<SessionPublic>(
      API_ENDPOINTS.SESSIONS.ARCHIVE(id)
    );
    return response.data;
  },
};
