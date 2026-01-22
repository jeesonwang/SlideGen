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

const { Text, Paragraph } = Typography;

interface EmbeddingConfigListProps {
  configs: EmbeddingConfigPublic[];
  loading?: boolean;
  onEdit: (config: EmbeddingConfigPublic) => void;
  onDelete: (id: string) => void;
  onTest: (config: EmbeddingConfigPublic) => void;
  onSetDefault: (id: string) => void;
}

export const EmbeddingConfigList: React.FC<EmbeddingConfigListProps> = ({
  configs,
  loading = false,
  onEdit,
  onDelete,
  onTest,
  onSetDefault,
}) => {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (configs.length === 0) {
    return (
      <Empty
        description="No embedding configurations yet"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Text type="secondary">
          Create your first embedding configuration for knowledge base search
        </Text>
      </Empty>
    );
  }

  return (
    <Row gutter={[16, 16]}>
      {configs.map((config) => (
        <Col xs={24} md={12} xl={8} key={config.id}>
          <Card
            title={
              <Space>
                <Text strong>{config.name}</Text>
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
              </Space>
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
                  onClick={() => onTest(config)}
                >
                  Test
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
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <div>
                <Text type="secondary">Provider: </Text>
                <Tag>{config.provider}</Tag>
              </div>
              <div>
                <Text type="secondary">Model: </Text>
                <Text code>{config.model_id}</Text>
              </div>
              {config.api_key && (
                <div>
                  <Text type="secondary">API Key: </Text>
                  <Text code>{config.api_key}</Text>
                </div>
              )}
              {config.dimensions && (
                <div>
                  <Text type="secondary">Dimensions: </Text>
                  <Text>{config.dimensions}</Text>
                </div>
              )}
              {config.base_url && (
                <div>
                  <Text type="secondary">Base URL: </Text>
                  <Text ellipsis style={{ maxWidth: 200 }}>
                    {config.base_url}
                  </Text>
                </div>
              )}
              {config.description && (
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  style={{ marginTop: 8, marginBottom: 0 }}
                >
                  {config.description}
                </Paragraph>
              )}
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );
};
