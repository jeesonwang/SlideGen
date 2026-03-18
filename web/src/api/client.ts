/**
 * Axios client configuration with JWT interceptors
 */

import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';
import type { ErrorResponse } from './types/common.types';
import { resolveApiBaseUrl } from './baseUrl';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(
    import.meta.env.VITE_API_BASE_URL,
    import.meta.env.DEV
  ),
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from Zustand store
    // This allows cleaner synchronization than raw localStorage access
    const { token } = useAuthStore.getState();

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      // Use store action to logout (clears state and localStorage)
      const { logout } = useAuthStore.getState();
      logout();

      // Only redirect if we're not already on the login page
      if (!window.location.pathname.includes('/login')) {
        // We can rely on the store update to trigger the redirect via ProtectedRoute
        // But forcing a check is safer if the user is in a non-protected route that uses API
        // window.location.href = '/login'; 
      }
    }

    // Handle other errors
    if (error.response?.data) {
      // Return structured error response
      return Promise.reject(error.response.data);
    }

    // Network or other errors
    return Promise.reject({
      detail: error.message || 'An unexpected error occurred',
    });
  }
);

export default apiClient;
