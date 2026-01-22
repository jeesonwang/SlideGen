/**
 * LLM Configuration Form component
 */

import { useEffect } from 'react';
import { Form, Input, InputNumber, Select, Button, Space, Collapse, Switch } from 'antd';
import { useLLMProviders, useLLMModels } from '../../hooks/useLLMConfigs';
import type { LLMConfigCreate } from '../../api/types/llmConfig.types';

const { TextArea } = Input;
const { Panel } = Collapse;

interface LLMConfigFormProps {
  initialValues?: Partial<LLMConfigCreate>;
  onSubmit: (values: Omit<LLMConfigCreate, 'user_id'>) => void;
  onCancel: () => void;
  loading?: boolean;
}

export const LLMConfigForm: React.FC<LLMConfigFormProps> = ({
  initialValues,
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const [form] = Form.useForm();
  const { data: providersData } = useLLMProviders();

  const selectedProvider = Form.useWatch('provider', form);
  const { data: modelsData } = useLLMModels(selectedProvider);

  // Reset model when provider changes
  useEffect(() => {
    if (selectedProvider && selectedProvider !== initialValues?.provider) {
      form.setFieldValue('model_id', undefined);
    }
  }, [selectedProvider, form, initialValues?.provider]);

  const handleFinish = (values: any) => {
    onSubmit(values);
  };

  const providerInfo = providersData?.providers.find(
    (p) => p.provider === selectedProvider
  );

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      initialValues={{
        temperature: 0.7,
        max_tokens: 4096,
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
        <Input placeholder="e.g., My GPT-4 Config" />
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
        <div className="mb-4 p-3 bg-gray-100 rounded">
          <div>{providerInfo.description}</div>
          {providerInfo.documentation_url && (
            <a href={providerInfo.documentation_url} target="_blank" rel="noopener noreferrer">
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
        >
          {modelsData?.models.map((model) => (
            <Select.Option key={model.model_id} value={model.model_id}>
              {model.name}
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

      <Collapse ghost>
        <Panel header="Advanced Settings" key="advanced">
          <Form.Item
            name="temperature"
            label="Temperature"
            tooltip="Controls randomness. Lower is more focused, higher is more creative."
          >
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="max_tokens"
            label="Max Tokens"
            tooltip="Maximum number of tokens to generate"
          >
            <InputNumber min={1} step={100} style={{ width: '100%' }} />
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

      <Form.Item style={{ marginTop: 24 }}>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            {initialValues ? 'Update' : 'Create'}
          </Button>
          <Button onClick={onCancel}>Cancel</Button>
        </Space>
      </Form.Item>
    </Form>
  );
};
