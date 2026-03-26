/**
 * Embedding Configuration types
 */

export const EmbeddingProvider = {
  OPENAI: 'openai',
  AZURE_OPENAI: 'azure_openai',
  OLLAMA: 'ollama',
  CUSTOM: 'custom',
} as const;

export type EmbeddingProvider = (typeof EmbeddingProvider)[keyof typeof EmbeddingProvider];

export interface EmbeddingConfigBase {
  name: string;
  provider: EmbeddingProvider;
  model_id: string;
  api_key?: string | null;
  base_url?: string | null;
  dimensions?: number | null;
  description?: string | null;
  extra_params?: Record<string, any> | null;
  is_active: boolean;
  is_default: boolean;
}

export interface EmbeddingConfigCreate extends EmbeddingConfigBase {
  user_id: string;
}

export interface EmbeddingConfigUpdate {
  name?: string;
  provider?: EmbeddingProvider;
  model_id?: string;
  api_key?: string | null;
  base_url?: string | null;
  dimensions?: number | null;
  is_active?: boolean;
  is_default?: boolean;
  description?: string | null;
  extra_params?: Record<string, any> | null;
}

export interface EmbeddingConfigPublic extends EmbeddingConfigBase {
  id: string;
  user_id: string;
}

export interface EmbeddingConfigsPublic {
  data: EmbeddingConfigPublic[];
  count: number;
}

export interface EmbeddingConfigTest {
  config_id?: string | null;
  provider: EmbeddingProvider;
  model_id: string;
  api_key?: string | null;
  base_url?: string | null;
  dimensions?: number | null;
  extra_params?: Record<string, any> | null;
  test_text?: string;
}

export interface EmbeddingConfigTestResult {
  success: boolean;
  embedding_dimension?: number | null;
  error?: string | null;
  latency?: number | null;
}

export interface EmbeddingProviderInfo {
  provider: EmbeddingProvider;
  name: string;
  description: string;
  requires_api_key: boolean;
  supports_custom_base_url: boolean;
  default_base_url?: string | null;
  documentation_url?: string | null;
}

export interface EmbeddingProvidersInfo {
  providers: EmbeddingProviderInfo[];
}

export interface AvailableEmbeddingModels {
  provider: EmbeddingProvider;
  models: Array<{ model_id: string; name: string; dimensions?: number }>;
}
