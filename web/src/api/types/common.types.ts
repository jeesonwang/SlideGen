export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonObject
  | JsonValue[];

export interface JsonObject {
  [key: string]: JsonValue;
}

/**
 * Common types used across the application
 */

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ErrorResponse {
  detail: string | JsonObject;
}

export interface PaginatedResponse<T> {
  data: T[];
  count: number;
}

export interface Message {
  message: string;
}
