/**
 * Embedding Configuration List component
 */

import { Card, Button, Space, Tag, Popconfirm, Typography, Empty, Spin, Row, Col, Tooltip } from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  StarOutlined,
  StarFilled,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { EmbeddingConfigPublic } from '../../api/types/embeddingConfig.types';
import { maskSecret } from './maskSecret';

const { Text, Paragraph } = Typography;

interface EmbeddingConfigListProps {
  configs: EmbeddingConfigPublic[];
  loading?: boolean;
  testingConfigId?: string | null;
  onEdit: (config: EmbeddingConfigPublic) => void;
  onDelete: (id: string) => void;
  onTest: (config: EmbeddingConfigPublic) => void;
  onSetDefault: (id: string) => void;
}

export const EmbeddingConfigList: React.FC<EmbeddingConfigListProps> = ({
  configs,
  loading = false,
  testingConfigId = null,
  onEdit,
  onDelete,
  onTest,
  onSetDefault,
}) => {
  if (loading) {
    return (
      <div className="text-center p-10">
        <Spin size="large" />
      </div>
    );
  }

  if (configs.length === 0) {
    return (
        <Empty
          description="No embedding configurations yet"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          className="rounded-2xl border border-dashed border-border/70 bg-surface-50 py-10"
        >
        <Text className="text-text-secondary">
          Create your first embedding configuration for knowledge base search
        </Text>
      </Empty>
    );
  }

  return (
    <Row gutter={[16, 16]}>
      {configs.map((config) => {
        const isTesting = testingConfigId === config.id;

        return (
        <Col xs={24} md={12} xl={8} key={config.id}>
          <Card
            className="modern-card h-full !rounded-2xl !border !border-border/70"
            styles={{
              header: {
                alignItems: 'flex-start',
              },
              title: {
                whiteSpace: 'normal',
                overflow: 'visible',
                textOverflow: 'unset',
              },
              extra: {
                alignSelf: 'flex-start',
              },
            }}
            title={
              <div className="flex flex-col gap-2 min-w-0">
                <Text strong className="!text-text-main">
                  {config.name}
                </Text>
                <div className="flex flex-wrap items-center gap-2">
                  {config.is_default && (
                    <Tag color="gold" icon={<StarFilled />}>
                      Default
                    </Tag>
                  )}
                  {config.is_active ? (
                    <Tag color="success" icon={<CheckCircleOutlined />}>
                      Active
                    </Tag>
                  ) : (
                    <Tag color="default">Inactive</Tag>
                  )}
                </div>
              </div>
            }
            extra={
              !config.is_default && (
                <Tooltip title="Set as default">
                  <Button
                    type="text"
                    icon={<StarOutlined />}
                    size="small"
                    onClick={() => onSetDefault(config.id)}
                  />
                </Tooltip>
              )
            }
            actions={[
              <Tooltip title="Test connection" key="test">
                <Button
                  type="text"
                  icon={<ThunderboltOutlined />}
                  loading={isTesting}
                  disabled={isTesting}
                  onClick={() => onTest(config)}
                >
                  {isTesting ? 'Testing...' : 'Test'}
                </Button>
              </Tooltip>,
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => onEdit(config)}
                key="edit"
              >
                Edit
              </Button>,
              <Popconfirm
                title="Delete configuration?"
                description="This action cannot be undone."
                onConfirm={() => onDelete(config.id)}
                okText="Delete"
                cancelText="Cancel"
                okButtonProps={{ danger: true }}
                key="delete"
              >
                <Button type="text" danger icon={<DeleteOutlined />}>
                  Delete
                </Button>
              </Popconfirm>,
            ]}
          >
            <Space direction="vertical" className="w-full" size="small">
              {isTesting && (
                <div className="rounded-xl border border-primary-500/20 bg-primary-500/8 px-3 py-2">
                  <Text className="text-primary-300">Waiting for model response...</Text>
                </div>
              )}
              <div>
                <Text className="text-text-secondary">Provider: </Text>
                <Tag>{config.provider}</Tag>
              </div>
              <div>
                <Text className="text-text-secondary">Model: </Text>
                <Text code>{config.model_id}</Text>
              </div>
              {config.api_key && (
                <div>
                  <Text className="text-text-secondary">API Key: </Text>
                  <Text code>{maskSecret(config.api_key)}</Text>
                </div>
              )}
              {config.dimensions && (
                <div>
                  <Text className="text-text-secondary">Dimensions: </Text>
                  <Text>{config.dimensions}</Text>
                </div>
              )}
              {config.base_url && (
                <div>
                  <Text className="text-text-secondary">Base URL: </Text>
                  <Text ellipsis className="max-w-[200px]">
                    {config.base_url}
                  </Text>
                </div>
              )}
              {config.description && (
                <Paragraph
                  ellipsis={{ rows: 2 }}
                  className="mt-2 mb-0 text-text-secondary"
                >
                  {config.description}
                </Paragraph>
              )}
            </Space>
          </Card>
        </Col>
      )})}
    </Row>
  );
};
