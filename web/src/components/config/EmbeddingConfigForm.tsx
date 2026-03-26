/**
 * Embedding Configuration Form component
 */

import { useEffect, useState } from 'react';
import { Form, Input, InputNumber, Select, Button, Space, Collapse, Switch, message } from 'antd';
import { useEmbeddingProviders, useFetchEmbeddingModels } from '../../hooks/useEmbeddingConfigs';
import type { AvailableEmbeddingModels, EmbeddingConfigCreate } from '../../api/types/embeddingConfig.types';

const { TextArea } = Input;
const { Panel } = Collapse;

interface EmbeddingConfigFormProps {
  initialValues?: Partial<EmbeddingConfigCreate>;
  onSubmit: (values: Omit<EmbeddingConfigCreate, 'user_id'>) => void;
  onCancel: () => void;
  loading?: boolean;
}

export const EmbeddingConfigForm: React.FC<EmbeddingConfigFormProps> = ({
  initialValues,
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const [form] = Form.useForm();
  const [availableModels, setAvailableModels] = useState<AvailableEmbeddingModels['models']>([]);
  const { data: providersData } = useEmbeddingProviders();
  const fetchModelsMutation = useFetchEmbeddingModels();

  const selectedProvider = Form.useWatch('provider', form);
  const selectedApiKey = Form.useWatch('api_key', form);
  const selectedBaseUrl = Form.useWatch('base_url', form);

  // Reset model when provider changes
  useEffect(() => {
    if (selectedProvider && selectedProvider !== initialValues?.provider) {
      form.setFieldValue('model_id', undefined);
      form.setFieldValue('dimensions', undefined);
      setAvailableModels([]);
    }
  }, [selectedProvider, form, initialValues?.provider]);

  useEffect(() => {
    setAvailableModels([]);
  }, [selectedProvider, selectedApiKey, selectedBaseUrl]);

  const handleFinish = (values: Omit<EmbeddingConfigCreate, 'user_id'>) => {
    onSubmit(values);
  };

  const providerInfo = providersData?.providers.find(
    (p) => p.provider === selectedProvider
  );

  const handleModelChange = (modelId: string) => {
    const model = availableModels.find((m) => m.model_id === modelId);
    if (model && 'dimensions' in model && model.dimensions) {
      form.setFieldValue('dimensions', model.dimensions);
    }
  };

  const canFetchModels = (() => {
    if (!selectedProvider) {
      return false;
    }

    if (providerInfo?.requires_api_key && !selectedApiKey) {
      return false;
    }

    if (selectedProvider === 'custom' && !selectedBaseUrl) {
      return false;
    }

    return true;
  })();

  const handleFetchModels = async () => {
    try {
      const values = form.getFieldsValue(['provider', 'api_key', 'base_url', 'extra_params']);
      const result = await fetchModelsMutation.mutateAsync({
        provider: values.provider,
        api_key: values.api_key,
        base_url: values.base_url,
        extra_params: values.extra_params,
      });

      setAvailableModels(result.models);

      if (result.models.length === 0) {
        message.warning('No models were returned. You can still enter a model ID manually.');
        return;
      }

      message.success(`Loaded ${result.models.length} models`);
    } catch {
      // Error message is already handled by the mutation
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      initialValues={{
        is_active: true,
        is_default: false,
        ...initialValues,
      }}
    >
      <Form.Item
        name="name"
        label="Configuration Name"
        rules={[{ required: true, message: 'Please enter a name' }]}
      >
        <Input placeholder="e.g., My OpenAI Embeddings" />
      </Form.Item>

      <Form.Item
        name="provider"
        label="Provider"
        rules={[{ required: true, message: 'Please select a provider' }]}
      >
        <Select placeholder="Select a provider">
          {providersData?.providers.map((provider) => (
            <Select.Option key={provider.provider} value={provider.provider}>
              {provider.name}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      {providerInfo && (
        <div className="mb-5 rounded-2xl border border-primary-500/15 bg-primary-500/8 p-4 text-sm text-text-secondary">
          <div className="font-medium text-text-main">{providerInfo.description}</div>
          {providerInfo.documentation_url && (
            <a
              href={providerInfo.documentation_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex text-primary-300 hover:text-primary-200"
            >
              View Documentation
            </a>
          )}
        </div>
      )}

      <Form.Item
        label="Model"
        extra="Click Fetch Models to load embedding models from the current provider configuration. Manual input remains available."
      >
        <Space.Compact block>
          <Form.Item
            name="model_id"
            noStyle
            rules={[{ required: true, message: 'Please select or enter a model' }]}
          >
            {availableModels.length > 0 ? (
              <Select
                placeholder="Select a model"
                showSearch
                optionFilterProp="label"
                options={availableModels.map((model) => ({
                  value: model.model_id,
                  label:
                    'dimensions' in model && model.dimensions
                      ? `${model.name} (${model.dimensions}d)`
                      : model.name,
                }))}
                onChange={handleModelChange}
              />
            ) : (
              <Input placeholder="Enter a model ID" />
            )}
          </Form.Item>
          <Button
            onClick={handleFetchModels}
            loading={fetchModelsMutation.isPending}
            disabled={!canFetchModels}
          >
            Fetch Models
          </Button>
        </Space.Compact>
      </Form.Item>

      {providerInfo?.requires_api_key && (
        <Form.Item
          name="api_key"
          label="API Key"
          rules={[
            {
              required: providerInfo.requires_api_key,
              message: 'Please enter your API key',
            },
          ]}
        >
          <Input.Password placeholder="sk-..." />
        </Form.Item>
      )}

      {providerInfo?.supports_custom_base_url && (
        <Form.Item name="base_url" label="Base URL (Optional)">
          <Input
            placeholder={providerInfo.default_base_url || 'https://api.example.com/v1'}
          />
        </Form.Item>
      )}

      <Collapse
        ghost
        className="rounded-2xl border border-white/10 bg-surface-100/30 px-4 py-2"
      >
        <Panel header="Advanced Settings" key="advanced">
          <Form.Item
            name="dimensions"
            label="Dimensions (Optional)"
            tooltip="Embedding dimensions. Leave empty to use model default."
          >
            <InputNumber min={1} step={1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="Optional description" />
          </Form.Item>

          <Form.Item name="is_active" label="Active" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item
            name="is_default"
            label="Set as Default"
            valuePropName="checked"
            tooltip="Use this configuration by default for new generations"
          >
            <Switch />
          </Form.Item>
        </Panel>
      </Collapse>

      <Form.Item className="!mb-0 !mt-8">
        <Space>
          <Button type="primary" htmlType="submit" loading={loading} className="!h-11 !rounded-xl !px-5 !font-semibold">
            {initialValues ? 'Update' : 'Create'}
          </Button>
          <Button onClick={onCancel} className="!h-11 !rounded-xl !px-5">Cancel</Button>
        </Space>
      </Form.Item>
    </Form>
  );
};
