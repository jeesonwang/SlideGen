import { Button, Empty, Input, Popconfirm, Tag, Typography } from 'antd';
import {
  CalendarOutlined,
  DeleteOutlined,
  FileTextOutlined,
  MessageOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import type { SessionPublic } from '../../api/types/session.types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { getSessionDisplayTitle } from '../chat/chatSessionTitle';
import { getSessionMetaLine, getSessionStatusPresentation } from './sessionPresentation';

dayjs.extend(relativeTime);

const { Search } = Input;
const { Text } = Typography;

interface SessionListProps {
  sessions: SessionPublic[];
  loading?: boolean;
  onView?: (session: SessionPublic) => void;
  onDelete: (id: string) => void;
  searchTerm?: string;
  onSearchChange?: (value: string) => void;
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  loading = false,
  onView,
  onDelete,
  searchTerm,
  onSearchChange,
}) => {
  return (
    <div className="space-y-5">
      {onSearchChange ? (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <Search
            placeholder="Search projects by title or topic"
            allowClear
            value={searchTerm}
            onChange={(event) => onSearchChange(event.target.value)}
            className="max-w-2xl"
            size="large"
            enterButton={<SearchOutlined />}
          />
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-border/70 bg-surface-100 px-3 py-1.5 text-sm text-text-secondary">
              {sessions.length} results
            </span>
            {searchTerm ? (
              <span className="rounded-full border border-primary-500/20 bg-primary-500/10 px-3 py-1.5 text-sm text-primary-600">
                Filtering: {searchTerm}
              </span>
            ) : null}
          </div>
        </div>
      ) : null}

      {sessions.length === 0 && !loading ? (
        <div className="rounded-[2rem] border border-dashed border-border/70 bg-surface-50 px-6 py-12">
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={searchTerm ? 'No matching projects found' : 'No presentation projects yet'}
          />
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => {
            const status = getSessionStatusPresentation(session.status);

            return (
              <article
                key={session.id}
                className="rounded-[1.75rem] border border-border/70 bg-background px-5 py-5 shadow-soft"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <Text strong className="!text-lg !text-text-main">
                        {getSessionDisplayTitle(session.title, session.topic)}
                      </Text>
                      <Tag color={status.color} className="!rounded-full !px-3">
                        {status.label}
                      </Tag>
                    </div>

                    <Text className="block text-sm leading-6 !text-text-secondary">
                      {getSessionMetaLine(session)}
                    </Text>

                    <div className="mt-4 flex flex-wrap gap-4 text-xs text-text-secondary">
                      <span className="inline-flex items-center gap-1">
                        <CalendarOutlined />
                        Updated {dayjs(session.update_time).fromNow()}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <FileTextOutlined />
                        {session.file_count} files
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <MessageOutlined />
                        {session.message_count} messages
                      </span>
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-2">
                    {onView ? (
                      <Button
                        type="primary"
                        onClick={() => onView(session)}
                        className="!h-10 !rounded-xl !px-4"
                      >
                        Continue editing
                      </Button>
                    ) : null}
                    <Popconfirm
                      title="Delete project?"
                      description="This action cannot be undone."
                      onConfirm={() => onDelete(session.id)}
                      okText="Delete"
                      cancelText="Cancel"
                      okButtonProps={{ danger: true }}
                    >
                      <Button
                        danger
                        icon={<DeleteOutlined />}
                        className="!h-10 !rounded-xl"
                      >
                        Delete
                      </Button>
                    </Popconfirm>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
};
