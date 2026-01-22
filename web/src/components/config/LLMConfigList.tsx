/**
 * LLM Configuration List component
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
import type { LLMConfigPublic } from '../../api/types/llmConfig.types';

const { Text, Paragraph } = Typography;

interface LLMConfigListProps {
  configs: LLMConfigPublic[];
  loading?: boolean;
  onEdit: (config: LLMConfigPublic) => void;
  onDelete: (id: string) => void;
  onTest: (config: LLMConfigPublic) => void;
  onSetDefault: (id: string) => void;
}

export const LLMConfigList: React.FC<LLMConfigListProps> = ({
  configs,
  loading = false,
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
        description="No LLM configurations yet"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Text type="secondary">
          Create your first LLM configuration to start generating presentations
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
            <Space direction="vertical" className="w-full" size="small">
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
              <div>
                <Text type="secondary">Temperature: </Text>
                <Text>{config.temperature}</Text>
              </div>
              <div>
                <Text type="secondary">Max Tokens: </Text>
                <Text>{config.max_tokens}</Text>
              </div>
              {config.base_url && (
                <div>
                  <Text type="secondary">Base URL: </Text>
                  <Text ellipsis className="max-w-[200px]">
                    {config.base_url}
                  </Text>
                </div>
              )}
              {config.description && (
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  className="mt-2 mb-0"
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
