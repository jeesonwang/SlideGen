/**
 * LLM Configuration Management Page
 */

import { useState } from 'react';
import { Button, Typography, Modal } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { LLMConfigList } from '../../components/config/LLMConfigList';
import { LLMConfigForm } from '../../components/config/LLMConfigForm';
import {
  useLLMConfigs,
  useCreateLLMConfig,
  useUpdateLLMConfig,
  useDeleteLLMConfig,
  useTestLLMConfig,
  useSetDefaultLLMConfig,
} from '../../hooks/useLLMConfigs';
import type {
  LLMConfigCreate,
  LLMConfigPublic,
} from '../../api/types/llmConfig.types';

const { Title, Text } = Typography;

export const LLMConfigPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<LLMConfigPublic | null>(null);

  const { data: configsData, isLoading } = useLLMConfigs();
  const createMutation = useCreateLLMConfig();
  const updateMutation = useUpdateLLMConfig();
  const deleteMutation = useDeleteLLMConfig();
  const testMutation = useTestLLMConfig();
  const setDefaultMutation = useSetDefaultLLMConfig();

  const configs = configsData?.data || [];

  const handleCreate = () => {
    setEditingConfig(null);
    setIsModalOpen(true);
  };

  const handleEdit = (config: LLMConfigPublic) => {
    setEditingConfig(config);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  const handleTest = async (config: LLMConfigPublic) => {
    await testMutation.mutateAsync({
      provider: config.provider,
      model_id: config.model_id,
      api_key: config.api_key || undefined,
      base_url: config.base_url || undefined,
      temperature: config.temperature,
      max_tokens: config.max_tokens || undefined,
      extra_params: config.extra_params || undefined,
      test_prompt: 'Hello, this is a test.',
    });
  };

  const handleSetDefault = async (id: string) => {
    await setDefaultMutation.mutateAsync(id);
  };

  const handleSubmit = async (values: Omit<LLMConfigCreate, 'user_id'>) => {
    try {
      if (editingConfig) {
        await updateMutation.mutateAsync({
          id: editingConfig.id,
          data: values,
        });
      } else {
        await createMutation.mutateAsync(values);
      }
      setIsModalOpen(false);
      setEditingConfig(null);
    } catch {
      // Error is already handled by the mutation
    }
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setEditingConfig(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-2xl border border-border/70 bg-surface-50 p-6 shadow-soft lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <Title level={3} className="!mb-0 !text-text-main">
            LLM Configurations
          </Title>
          <Text className="text-text-secondary">
            Manage language model settings for presentation generation, including defaults, connection tests, and advanced parameters.
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} className="!h-11 !rounded-xl !px-5 !font-semibold">
          Add Configuration
        </Button>
      </div>

      <LLMConfigList
        configs={configs}
        loading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onTest={handleTest}
        onSetDefault={handleSetDefault}
      />

      <Modal
        title={editingConfig ? 'Edit LLM Configuration' : 'Create LLM Configuration'}
        open={isModalOpen}
        onCancel={handleCancel}
        footer={null}
        width={600}
        styles={{
          body: {
            paddingTop: 12,
          },
        }}
        destroyOnClose
      >
        <LLMConfigForm
          initialValues={editingConfig || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          loading={createMutation.isPending || updateMutation.isPending}
        />
      </Modal>
    </div>
  );
};
