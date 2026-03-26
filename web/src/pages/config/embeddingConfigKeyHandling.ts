import type {
  EmbeddingConfigPublic,
  EmbeddingConfigTest,
  EmbeddingConfigUpdate,
} from '../../api/types/embeddingConfig.types';

export const isMaskedApiKey = (value?: string | null): boolean =>
  Boolean(value) && value!.startsWith('***');

export const sanitizeEmbeddingConfigSubmitValues = (
  values: EmbeddingConfigUpdate,
  initialValues?: Partial<EmbeddingConfigPublic> | null
): EmbeddingConfigUpdate => {
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

export const buildEmbeddingConfigTestPayload = (
  config: EmbeddingConfigPublic,
  testText = 'This is a test sentence for embedding.'
): EmbeddingConfigTest => ({
  config_id: config.id,
  provider: config.provider,
  model_id: config.model_id,
  api_key: isMaskedApiKey(config.api_key) ? undefined : config.api_key || undefined,
  base_url: config.base_url || undefined,
  dimensions: config.dimensions || undefined,
  extra_params: config.extra_params || undefined,
  test_text: testText,
});
