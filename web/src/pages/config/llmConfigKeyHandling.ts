import type {
  LLMConfigPublic,
  LLMConfigTest,
  LLMConfigUpdate,
} from '../../api/types/llmConfig.types';

export const isMaskedApiKey = (value?: string | null): boolean =>
  Boolean(value) && value!.startsWith('***');

export const sanitizeLLMConfigSubmitValues = (
  values: LLMConfigUpdate,
  initialValues?: Partial<LLMConfigPublic> | null
): LLMConfigUpdate => {
  if (!isMaskedApiKey(values.api_key)) {
    return values;
  }

  if (values.api_key === initialValues?.api_key) {
    return {
      ...values,
      api_key: undefined,
    };
  }

  return values;
};

export const buildLLMConfigTestPayload = (
  config: LLMConfigPublic,
  testPrompt = 'Hello, this is a test.'
): LLMConfigTest => ({
  config_id: config.id,
  provider: config.provider,
  model_id: config.model_id,
  api_key: isMaskedApiKey(config.api_key) ? undefined : config.api_key || undefined,
  base_url: config.base_url || undefined,
  temperature: config.temperature,
  max_tokens: config.max_tokens || undefined,
  extra_params: config.extra_params || undefined,
  test_prompt: testPrompt,
});
