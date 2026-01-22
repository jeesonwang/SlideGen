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
import type { EmbeddingConfigPublic } from '../../api/types/embeddingConfig.types';

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

  const handleSubmit = async (values: any) => {
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
    } catch (error) {
      // Error is already handled by the mutation
    }
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setEditingConfig(null);
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <div>
          <Title level={2} style={{ margin: 0 }}>
            Embedding Configurations
          </Title>
          <Text type="secondary">
            Manage your embedding model configurations for knowledge base search
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
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
