import { Button, Popconfirm, Tag, Tooltip, Typography } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FileMarkdownOutlined,
  FilePdfOutlined,
  FileTextOutlined,
  FileWordOutlined,
} from '@ant-design/icons';
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
      return <FilePdfOutlined className="text-text-secondary text-xl" />;
    }
    if (contentType?.includes('word') || filename?.endsWith('.docx')) {
      return <FileWordOutlined className="text-text-secondary text-xl" />;
    }
    if (filename?.endsWith('.md')) {
      return <FileMarkdownOutlined className="text-text-secondary text-xl" />;
    }
    return <FileTextOutlined className="text-text-secondary text-xl" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const index = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round((bytes / 1024 ** index) * 100) / 100} ${units[index]}`;
  };

  const getStatusTag = (file: FileMetadataPublic) => {
    if (file.parse_error) {
      return (
        <Tooltip title={file.parse_error}>
          <Tag icon={<CloseCircleOutlined />} color="error" className="!rounded-full !px-3">
            Failed
          </Tag>
        </Tooltip>
      );
    }
    if (file.parsed) {
      return (
        <Tag icon={<CheckCircleOutlined />} color="success" className="!rounded-full !px-3">
          Ready
        </Tag>
      );
    }
    return (
      <Tag className="!rounded-full !border-border/70 !bg-surface-100 !px-3 !text-text-secondary">
        Processing
      </Tag>
    );
  };

  if (loading) {
    return <div className="py-8 text-sm text-text-secondary">Loading references...</div>;
  }

  return (
    <div className="space-y-3">
      {files.map((file) => (
        <article
          key={file.id}
          className="flex flex-col gap-4 rounded-[1.5rem] border border-border/70 bg-background px-4 py-4 shadow-soft workbench-muted-panel sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex min-w-0 flex-1 items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-surface-100">
              {getFileIcon(file.content_type, file.filename)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Text strong className="!text-base !text-text-main">
                  {file.filename}
                </Text>
                {getStatusTag(file)}
              </div>
              <div className="flex flex-wrap gap-4 text-xs text-text-secondary">
                <span>{formatFileSize(file.file_size)}</span>
                <span>Uploaded {dayjs(file.create_time).fromNow()}</span>
                {file.content_type ? <span>{file.content_type}</span> : null}
              </div>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <Button
              icon={<DownloadOutlined />}
              onClick={() => onDownload(file)}
              className="!h-10 !rounded-xl !border-border/70 !bg-surface-100 !text-text-main"
            >
              Download
            </Button>
            <Popconfirm
              title="Remove reference?"
              description="This action cannot be undone."
              onConfirm={() => onDelete(file.id)}
              okText="Remove"
              cancelText="Cancel"
              okButtonProps={{ danger: true }}
            >
              <Button danger icon={<DeleteOutlined />} className="!h-10 !rounded-xl">
                Remove
              </Button>
            </Popconfirm>
          </div>
        </article>
      ))}
    </div>
  );
};
