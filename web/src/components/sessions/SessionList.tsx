/**
 * Session List component
 */

import { Table, Tag, Button, Space, Popconfirm, Typography, Input } from 'antd';
import {
  EyeOutlined,
  DeleteOutlined,
  InboxOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { SessionPublic } from '../../api/types/session.types';
import { SessionStatus } from '../../api/types/session.types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Text } = Typography;
const { Search } = Input;

interface SessionListProps {
  sessions: SessionPublic[];
  loading?: boolean;
  onView?: (session: SessionPublic) => void;
  onDelete: (id: string) => void;
  onArchive: (id: string) => void;
  searchTerm?: string;
  onSearchChange?: (value: string) => void;
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  loading = false,
  onView,
  onDelete,
  onArchive,
  searchTerm,
  onSearchChange,
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case SessionStatus.ACTIVE:
        return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
      case SessionStatus.COMPLETED:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case SessionStatus.FAILED:
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <InboxOutlined />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case SessionStatus.ACTIVE:
        return 'processing';
      case SessionStatus.COMPLETED:
        return 'success';
      case SessionStatus.FAILED:
        return 'error';
      case SessionStatus.ARCHIVED:
        return 'default';
      default:
        return 'default';
    }
  };

  const columns: ColumnsType<SessionPublic> = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: SessionPublic) => (
        <div>
          <Text strong>{title}</Text>
          {record.topic && (
            <div>
              <Text type="secondary" ellipsis style={{ fontSize: 12 }}>
                {record.topic}
              </Text>
            </div>
          )}
        </div>
      ),
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => (
        <Tag icon={getStatusIcon(status)} color={getStatusColor(status)}>
          {status}
        </Tag>
      ),
      filters: [
        { text: 'Active', value: SessionStatus.ACTIVE },
        { text: 'Completed', value: SessionStatus.COMPLETED },
        { text: 'Failed', value: SessionStatus.FAILED },
        { text: 'Archived', value: SessionStatus.ARCHIVED },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Files',
      dataIndex: 'file_count',
      key: 'file_count',
      width: 80,
      align: 'center',
      render: (count: number) => <Text>{count}</Text>,
    },
    {
      title: 'Messages',
      dataIndex: 'message_count',
      key: 'message_count',
      width: 100,
      align: 'center',
      render: (count: number) => <Text>{count}</Text>,
    },
    {
      title: 'Created',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      render: (time: string) => (
        <Text type="secondary">{dayjs(time).fromNow()}</Text>
      ),
      sorter: (a, b) =>
        dayjs(a.create_time).unix() - dayjs(b.create_time).unix(),
      defaultSortOrder: 'descend',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          {onView && (
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onView(record)}
            >
              View
            </Button>
          )}
          {record.status !== SessionStatus.ARCHIVED && (
            <Button
              type="link"
              size="small"
              icon={<InboxOutlined />}
              onClick={() => onArchive(record.id)}
            >
              Archive
            </Button>
          )}
          <Popconfirm
            title="Delete session?"
            description="This action cannot be undone."
            onConfirm={() => onDelete(record.id)}
            okText="Delete"
            cancelText="Cancel"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {onSearchChange && (
        <div style={{ marginBottom: 16 }}>
          <Search
            placeholder="Search sessions by title or topic..."
            allowClear
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{ maxWidth: 400 }}
          />
        </div>
      )}
      <Table
        columns={columns}
        dataSource={sessions}
        rowKey="id"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} sessions`,
        }}
      />
    </div>
  );
};
