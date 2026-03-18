/**
 * Session List component
 */

import { Table, Tag, Button, Popconfirm, Typography, Input, Dropdown, Empty } from 'antd';
import {
  EyeOutlined,
  DeleteOutlined,
  InboxOutlined,
  MoreOutlined,
  MessageOutlined,
  FileTextOutlined,
  CalendarOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { SessionPublic } from '../../api/types/session.types';
import { SessionStatus } from '../../api/types/session.types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { getSessionMetaLine, getSessionStatusPresentation } from './sessionPresentation';

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
  const columns: ColumnsType<SessionPublic> = [
    {
      title: 'Session',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: SessionPublic) => (
        <div className="space-y-1.5">
          <Text strong className="!text-text-main !text-base">{title}</Text>
          <div className="flex items-center gap-3 text-xs text-text-muted">
            <span className="inline-flex items-center gap-1">
              <MessageOutlined />
              {record.message_count} messages
            </span>
            <span className="inline-flex items-center gap-1">
              <FileTextOutlined />
              {record.file_count} files
            </span>
          </div>
          <Text className="block text-sm !text-text-muted" ellipsis>
            {getSessionMetaLine(record)}
          </Text>
        </div>
      ),
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (status: string) => {
        const presentation = getSessionStatusPresentation(status);
        const Icon = presentation.icon;
        return (
        <Tag icon={<Icon />} color={presentation.color} className="!rounded-full !px-3 !py-1 !text-sm">
          {presentation.label}
        </Tag>
      );
      },
      filters: [
        { text: 'Active', value: SessionStatus.ACTIVE },
        { text: 'Completed', value: SessionStatus.COMPLETED },
        { text: 'Failed', value: SessionStatus.FAILED },
        { text: 'Archived', value: SessionStatus.ARCHIVED },
        { text: 'Deleted', value: SessionStatus.DELETED },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Files',
      dataIndex: 'file_count',
      key: 'file_count',
      width: 90,
      align: 'center',
      render: (count: number) => <Text className="!text-text-main">{count}</Text>,
    },
    {
      title: 'Messages',
      dataIndex: 'message_count',
      key: 'message_count',
      width: 110,
      align: 'center',
      render: (count: number) => <Text className="!text-text-main">{count}</Text>,
    },
    {
      title: 'Created',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (time: string) => (
        <div className="space-y-1">
          <Text className="block !text-text-main">{dayjs(time).fromNow()}</Text>
          <Text className="inline-flex items-center gap-1 text-xs !text-text-muted">
            <CalendarOutlined />
            {dayjs(time).format('YYYY/M/D')}
          </Text>
        </div>
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
        <div className="flex items-center justify-end gap-2">
          {onView && (
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onView(record)}
              className="!px-0 !text-primary-400 hover:!text-primary-300"
            >
              View
            </Button>
          )}
          {record.status !== SessionStatus.DELETED ? (
            <Dropdown
              trigger={['click']}
              menu={{
                items: [
                  ...(record.status !== SessionStatus.ARCHIVED
                    ? [{
                        key: 'archive',
                        label: 'Archive',
                        icon: <InboxOutlined />,
                        onClick: () => onArchive(record.id),
                      }]
                    : []),
                  {
                    key: 'delete',
                    label: (
                      <Popconfirm
                        title="Delete session?"
                        description="This action cannot be undone."
                        onConfirm={() => onDelete(record.id)}
                        okText="Delete"
                        cancelText="Cancel"
                        okButtonProps={{ danger: true }}
                      >
                        <span>Delete</span>
                      </Popconfirm>
                    ),
                    icon: <DeleteOutlined />,
                    danger: true,
                  },
                ],
              }}
            >
              <Button
                size="small"
                icon={<MoreOutlined />}
                className="!rounded-lg !border-border/70 !bg-surface-100 !text-text-secondary hover:!border-border hover:!bg-surface-200"
              />
            </Dropdown>
          ) : null}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      {onSearchChange && (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <Search
            placeholder="Search sessions by title or topic"
            allowClear
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="max-w-2xl"
            size="large"
            enterButton={<SearchOutlined />}
          />
          <div className="flex items-center gap-3">
            <span className="rounded-full border border-border/70 bg-surface-100 px-3 py-1.5 text-sm text-text-secondary">
              {sessions.length} results
            </span>
            {searchTerm ? (
              <span className="rounded-full border border-primary-500/20 bg-primary-500/10 px-3 py-1.5 text-sm text-primary-300">
                Filtering: {searchTerm}
              </span>
            ) : null}
          </div>
        </div>
      )}
      <Table
        className="session-table [&_.ant-table-tbody>tr]:cursor-default"
        columns={columns}
        dataSource={sessions}
        rowKey="id"
        loading={loading}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                searchTerm ? '没有找到符合条件的会话' : '暂无会话记录'
                
              }
            />
          ),
        }}
        pagination={{
          pageSize: 10,
          showSizeChanger: false,
          showTotal: (total) => `Total ${total} sessions`,
        }}
        scroll={{ x: 980 }}
      />
    </div>
  );
};
