/**
 * User API endpoints
 */

import apiClient from '../client';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  UserPublic,
  UserUpdate,
  UpdatePassword,
} from '../types/auth.types';
import type { Message } from '../types/common.types';

export const userApi = {
  /**
   * Get current user information
   */
  getMe: async (): Promise<UserPublic> => {
    const response = await apiClient.get<UserPublic>(API_ENDPOINTS.USER.ME);
    return response.data;
  },

  /**
   * Update current user information
   */
  updateMe: async (data: UserUpdate): Promise<UserPublic> => {
    const response = await apiClient.patch<UserPublic>(
      API_ENDPOINTS.USER.UPDATE_ME,
      data
    );
    return response.data;
  },

  /**
   * Update user password
   */
  updatePassword: async (data: UpdatePassword): Promise<Message> => {
    const response = await apiClient.patch<Message>(
      API_ENDPOINTS.USER.UPDATE_PASSWORD,
      data
    );
    return response.data;
  },
};
