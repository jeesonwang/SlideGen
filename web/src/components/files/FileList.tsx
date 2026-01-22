/**
 * File List component
 */

import { Table, Button, Space, Popconfirm, Typography, Tag, Tooltip } from 'antd';
import {
  DeleteOutlined,
  DownloadOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileMarkdownOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { FileMetadataPublic } from '../../api/types/file.types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Text } = Typography;

interface FileListProps {
  files: FileMetadataPublic[];
  loading?: boolean;
  onDelete: (id: string) => void;
  onDownload: (file: FileMetadataPublic) => void;
}

export const FileList: React.FC<FileListProps> = ({
  files,
  loading = false,
  onDelete,
  onDownload,
}) => {
  const getFileIcon = (contentType?: string | null, filename?: string) => {
    if (contentType?.includes('pdf')) {
      return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />;
    }
    if (contentType?.includes('word') || filename?.endsWith('.docx')) {
      return <FileWordOutlined style={{ color: '#1890ff', fontSize: 20 }} />;
    }
    if (filename?.endsWith('.md')) {
      return <FileMarkdownOutlined style={{ color: '#52c41a', fontSize: 20 }} />;
    }
    return <FileTextOutlined style={{ color: '#8c8c8c', fontSize: 20 }} />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const columns: ColumnsType<FileMetadataPublic> = [
    {
      title: 'File',
      dataIndex: 'filename',
      key: 'filename',
      render: (filename: string, record: FileMetadataPublic) => (
        <Space>
          {getFileIcon(record.content_type, filename)}
          <div>
            <Text strong>{filename}</Text>
            {record.content_type && (
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {record.content_type}
                </Text>
              </div>
            )}
          </div>
        </Space>
      ),
      ellipsis: true,
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => <Text>{formatFileSize(size)}</Text>,
      sorter: (a, b) => a.file_size - b.file_size,
    },
    {
      title: 'Status',
      dataIndex: 'parsed',
      key: 'parsed',
      width: 120,
      render: (parsed: boolean, record: FileMetadataPublic) => {
        if (record.parse_error) {
          return (
            <Tooltip title={record.parse_error}>
              <Tag icon={<CloseCircleOutlined />} color="error">
                Failed
              </Tag>
            </Tooltip>
          );
        }
        if (parsed) {
          return (
            <Tag icon={<CheckCircleOutlined />} color="success">
              Parsed
            </Tag>
          );
        }
        return <Tag color="default">Pending</Tag>;
      },
      filters: [
        { text: 'Parsed', value: true },
        { text: 'Failed', value: false },
      ],
      onFilter: (value, record) => {
        if (value === true) return record.parsed;
        return !record.parsed || !!record.parse_error;
      },
    },
    {
      title: 'Uploaded',
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
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => onDownload(record)}
          >
            Download
          </Button>
          <Popconfirm
            title="Delete file?"
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
    <Table
      columns={columns}
      dataSource={files}
      rowKey="id"
      loading={loading}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showTotal: (total) => `Total ${total} files`,
      }}
    />
  );
};
