/**
 * Embedding Configuration Management Page
 */

import { useState } from 'react';
import { Button, Typography, Modal } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { EmbeddingConfigList } from '../../components/config/EmbeddingConfigList';
import { EmbeddingConfigForm } from '../../components/config/EmbeddingConfigForm';
import {
  useEmbeddingConfigs,
  useCreateEmbeddingConfig,
  useUpdateEmbeddingConfig,
  useDeleteEmbeddingConfig,
  useTestEmbeddingConfig,
  useSetDefaultEmbeddingConfig,
} from '../../hooks/useEmbeddingConfigs';
import type {
  EmbeddingConfigCreate,
  EmbeddingConfigPublic,
} from '../../api/types/embeddingConfig.types';

const { Title, Text } = Typography;

export const EmbeddingConfigPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<EmbeddingConfigPublic | null>(null);

  const { data: configsData, isLoading } = useEmbeddingConfigs();
  const createMutation = useCreateEmbeddingConfig();
  const updateMutation = useUpdateEmbeddingConfig();
  const deleteMutation = useDeleteEmbeddingConfig();
  const testMutation = useTestEmbeddingConfig();
  const setDefaultMutation = useSetDefaultEmbeddingConfig();

  const configs = configsData?.data || [];

  const handleCreate = () => {
    setEditingConfig(null);
    setIsModalOpen(true);
  };

  const handleEdit = (config: EmbeddingConfigPublic) => {
    setEditingConfig(config);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  const handleTest = async (config: EmbeddingConfigPublic) => {
    await testMutation.mutateAsync({
      provider: config.provider,
      model_id: config.model_id,
      api_key: config.api_key || undefined,
      base_url: config.base_url || undefined,
      dimensions: config.dimensions || undefined,
      extra_params: config.extra_params || undefined,
      test_text: 'This is a test sentence for embedding.',
    });
  };

  const handleSetDefault = async (id: string) => {
    await setDefaultMutation.mutateAsync(id);
  };

  const handleSubmit = async (values: Omit<EmbeddingConfigCreate, 'user_id'>) => {
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
            Embedding Configurations
          </Title>
          <Text className="text-text-secondary">
            Manage embedding model settings for knowledge-base retrieval and semantic search, including defaults and dimensions.
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} className="!h-11 !rounded-xl !px-5 !font-semibold">
          Add Configuration
        </Button>
      </div>

      <EmbeddingConfigList
        configs={configs}
        loading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onTest={handleTest}
        onSetDefault={handleSetDefault}
      />

      <Modal
        title={
          editingConfig
            ? 'Edit Embedding Configuration'
            : 'Create Embedding Configuration'
        }
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
        <EmbeddingConfigForm
          initialValues={editingConfig || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          loading={createMutation.isPending || updateMutation.isPending}
        />
      </Modal>
    </div>
  );
};
