/**
 * LLM Configuration types
 */

export const LLMProvider = {
  OPENAI: 'openai',
  OPENROUTER: 'openrouter',
  ANTHROPIC: 'anthropic',
  AZURE_OPENAI: 'azure_openai',
  OLLAMA: 'ollama',
  CUSTOM: 'custom',
} as const;

export type LLMProvider = (typeof LLMProvider)[keyof typeof LLMProvider];

export interface LLMConfigBase {
  name: string;
  provider: LLMProvider;
  model_id: string;
  api_key?: string | null;
  base_url?: string | null;
  temperature: number;
  max_tokens: number;
  description?: string | null;
  extra_params?: Record<string, any> | null;
  is_active: boolean;
  is_default: boolean;
}

export interface LLMConfigCreate extends LLMConfigBase {
  user_id: string;
}

export interface LLMConfigUpdate {
  name?: string;
  provider?: LLMProvider;
  model_id?: string;
  api_key?: string | null;
  base_url?: string | null;
  temperature?: number;
  max_tokens?: number;
  is_active?: boolean;
  is_default?: boolean;
  description?: string | null;
  extra_params?: Record<string, any> | null;
}

export interface LLMConfigPublic extends LLMConfigBase {
  id: string;
  user_id: string;
}

export interface LLMConfigsPublic {
  data: LLMConfigPublic[];
  count: number;
}

export interface LLMConfigTest {
  provider: LLMProvider;
  model_id: string;
  api_key?: string | null;
  base_url?: string | null;
  temperature: number;
  max_tokens?: number | null;
  extra_params?: Record<string, any> | null;
  test_prompt?: string;
}

export interface LLMConfigTestResult {
  success: boolean;
  response?: string | null;
  error?: string | null;
  latency?: number | null;
}

export interface LLMProviderInfo {
  provider: LLMProvider;
  name: string;
  description: string;
  requires_api_key: boolean;
  supports_custom_base_url: boolean;
  default_base_url?: string | null;
  documentation_url?: string | null;
}

export interface LLMProvidersInfo {
  providers: LLMProviderInfo[];
}

export interface AvailableModels {
  provider: LLMProvider;
  models: Array<{ model_id: string; name: string }>;
}
