/**
 * Application constants
 */

// API Endpoints
export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: '/api/v1/login/access-token',
    SIGNUP: '/api/v1/user/signup',
    TEST_TOKEN: '/api/v1/login/test-token',
  },
  // LLM Config
  LLM_CONFIG: {
    LIST: '/api/v1/llm-config',
    CREATE: '/api/v1/llm-config',
    GET: (id: string) => `/api/v1/llm-config/${id}`,
    UPDATE: (id: string) => `/api/v1/llm-config/${id}`,
    DELETE: (id: string) => `/api/v1/llm-config/${id}`,
    TEST: '/api/v1/llm-config/test',
    SET_DEFAULT: (id: string) => `/api/v1/llm-config/${id}/set-default`,
    PROVIDERS: '/api/v1/llm-config/providers',
    MODELS: (provider: string) => `/api/v1/llm-config/providers/${provider}/models`,
  },
  // Embedding Config
  EMBEDDING_CONFIG: {
    LIST: '/api/v1/embedding-config',
    CREATE: '/api/v1/embedding-config',
    GET: (id: string) => `/api/v1/embedding-config/${id}`,
    UPDATE: (id: string) => `/api/v1/embedding-config/${id}`,
    DELETE: (id: string) => `/api/v1/embedding-config/${id}`,
    TEST: '/api/v1/embedding-config/test',
    SET_DEFAULT: (id: string) => `/api/v1/embedding-config/${id}/set-default`,
    PROVIDERS: '/api/v1/embedding-config/providers',
    MODELS: (provider: string) => `/api/v1/embedding-config/providers/${provider}/models`,
  },
  // Sessions
  SESSIONS: {
    LIST: '/api/v1/sessions',
    CREATE: '/api/v1/sessions',
    GET: (id: string) => `/api/v1/sessions/${id}`,
    UPDATE: (id: string) => `/api/v1/sessions/${id}`,
    DELETE: (id: string) => `/api/v1/sessions/${id}`,
    ARCHIVE: (id: string) => `/api/v1/sessions/${id}/archive`,
  },
  // Files
  FILES: {
    UPLOAD: '/api/v1/files/upload',
    UPLOAD_MULTIPLE: '/api/v1/files/upload-multiple',
    LIST: '/api/v1/files',
    DELETE: (id: string) => `/api/v1/files/${id}`,
    DOWNLOAD: (id: string) => `/api/v1/files/${id}/download`,
  },
  // SlideGen
  SLIDEGEN: {
    GENERATE_MARKDOWN_STREAM: '/api/v1/slidegen/generate-markdown-stream',
    GENERATE_PPTX_FROM_MARKDOWN: '/api/v1/slidegen/generate-pptx-from-markdown',
    DOWNLOAD: (taskId: string) => `/api/v1/slidegen/download/${taskId}`,
  },
  // User
  USER: {
    ME: '/api/v1/user/me',
    UPDATE_ME: '/api/v1/user/me',
    UPDATE_PASSWORD: '/api/v1/user/me/password',
  },
};

// Application defaults
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'SlideGen';

// Local storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  USER: 'user',
  THEME: 'theme',
};

// Generation defaults
export const GENERATION_DEFAULTS = {
  TONE: 'default',
  VERBOSITY: 'standard',
  N_SLIDES: 8,
  LANGUAGE: 'English',
  TEMPLATE: 'general',
  EXPORT_AS: 'pptx' as const,
  INCLUDE_TOC: false,
  INCLUDE_TITLE_SLIDE: true,
  WEB_SEARCH: false,
};
