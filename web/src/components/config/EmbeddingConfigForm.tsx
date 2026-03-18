/**
 * Embedding Configuration Form component
 */

import { useEffect } from 'react';
import { Form, Input, InputNumber, Select, Button, Space, Collapse, Switch } from 'antd';
import { useEmbeddingProviders, useEmbeddingModels } from '../../hooks/useEmbeddingConfigs';
import type { EmbeddingConfigCreate } from '../../api/types/embeddingConfig.types';

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
  const { data: providersData } = useEmbeddingProviders();

  const selectedProvider = Form.useWatch('provider', form);
  const { data: modelsData } = useEmbeddingModels(selectedProvider);

  // Reset model when provider changes
  useEffect(() => {
    if (selectedProvider && selectedProvider !== initialValues?.provider) {
      form.setFieldValue('model_id', undefined);
      form.setFieldValue('dimensions', undefined);
    }
  }, [selectedProvider, form, initialValues?.provider]);

  const handleFinish = (values: Omit<EmbeddingConfigCreate, 'user_id'>) => {
    onSubmit(values);
  };

  const providerInfo = providersData?.providers.find(
    (p) => p.provider === selectedProvider
  );

  const handleModelChange = (modelId: string) => {
    const model = modelsData?.models.find((m) => m.model_id === modelId);
    if (model && 'dimensions' in model && model.dimensions) {
      form.setFieldValue('dimensions', model.dimensions);
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
        name="model_id"
        label="Model"
        rules={[{ required: true, message: 'Please select or enter a model' }]}
      >
        <Select
          placeholder="Select or type a model ID"
          showSearch
          mode={modelsData?.models.length ? undefined : 'tags'}
          loading={!modelsData && !!selectedProvider}
          onChange={handleModelChange}
        >
          {modelsData?.models.map((model) => (
            <Select.Option key={model.model_id} value={model.model_id}>
              {model.name}
              {'dimensions' in model && model.dimensions && ` (${model.dimensions}d)`}
            </Select.Option>
          ))}
        </Select>
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
