/**
 * Common types used across the application
 */

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ErrorResponse {
  detail: string | Record<string, any>;
}

export interface PaginatedResponse<T> {
  data: T[];
  count: number;
}

export interface Message {
  message: string;
}
