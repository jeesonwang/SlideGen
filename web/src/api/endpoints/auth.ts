/**
 * Authentication API endpoints
 */

import apiClient from '../client';
import { API_ENDPOINTS } from '../../utils/constants';
import type {
  Token,
  UserPublic,
  UserRegister,
  LoginRequest,
} from '../types/auth.types';

export const authApi = {
  /**
   * Login with email and password
   */
  login: async (credentials: LoginRequest): Promise<Token> => {
    // FastAPI OAuth2 expects form data for login
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await apiClient.post<Token>(
      API_ENDPOINTS.AUTH.LOGIN,
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    return response.data;
  },

  /**
   * Register a new user
   */
  signup: async (userData: UserRegister): Promise<UserPublic> => {
    const response = await apiClient.post<UserPublic>(
      API_ENDPOINTS.AUTH.SIGNUP,
      userData
    );
    return response.data;
  },

  /**
   * Test if the current token is valid
   */
  testToken: async (): Promise<UserPublic> => {
    const response = await apiClient.post<UserPublic>(
      API_ENDPOINTS.AUTH.TEST_TOKEN
    );
    return response.data;
  },
};
