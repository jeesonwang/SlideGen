/**
 * Sessions Management Page
 */

import { useState, useMemo } from 'react';
import { Typography, Button, Space } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { SessionList } from '../../components/sessions/SessionList';
import { useSessions, useDeleteSession } from '../../hooks/useSessions';
import { useChatStore } from '../../store/chatStore';
import {
  SessionStatus,
  type SessionPublic,
} from '../../api/types/session.types';
import { getSessionSummary } from '../../components/sessions/sessionPresentation';
import {
  getSessionsPageContainerClassName,
  getSessionsPageContentClassName,
} from './sessionsPageLayout';

const { Title, Text } = Typography;

export const SessionsPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const { setCurrentSession, loadMessages } = useChatStore();

  const { data: sessionsData, isLoading, refetch } = useSessions();
  const deleteMutation = useDeleteSession();

  // Filter sessions by search term
  const filteredSessions = useMemo(() => {
    const sessions =
      sessionsData?.data.filter(
        (session) =>
          session.status !== SessionStatus.ARCHIVED &&
          session.status !== SessionStatus.DELETED
      ) || [];
    if (!searchTerm) return sessions;

    const lowerSearch = searchTerm.toLowerCase();
    return sessions.filter(
      (session) =>
        session.title.toLowerCase().includes(lowerSearch) ||
        session.topic?.toLowerCase().includes(lowerSearch)
    );
  }, [sessionsData?.data, searchTerm]);
  const summary = useMemo(
    () => getSessionSummary(filteredSessions),
    [filteredSessions]
  );

  const handleView = (session: SessionPublic) => {
    setCurrentSession(session.id);
    loadMessages(session.id);
    navigate('/generate');
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  const handleCreateNew = () => {
    navigate('/generate');
  };

  const handleRefresh = () => {
    refetch();
  };

  return (
    <div className={`${getSessionsPageContainerClassName()} workbench-page`}>
      <div className={getSessionsPageContentClassName()}>
        <div className="flex flex-col gap-5 rounded-[2rem] border border-border/70 bg-surface-50 p-6 shadow-soft workbench-panel lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-text-secondary">
              Project archive
            </div>
            <Title level={2} className="!mb-0 !text-text-main">
              Projects
            </Title>
            <Text className="block max-w-3xl leading-relaxed text-text-secondary">
              Manage your presentation projects, monitor status, and jump back into active work.
            </Text>
            <div className="flex flex-wrap gap-3">
              <span className="rounded-full border border-border/70 bg-surface-100 px-3 py-1.5 text-sm text-text-secondary">
                Total {summary.total}
              </span>
              <span className="rounded-full border border-primary-500/20 bg-primary-500/10 px-3 py-1.5 text-sm text-primary-600">
                Active {summary.active}
              </span>
            </div>
          </div>
          <Space size="middle">
            <Button icon={<ReloadOutlined />} onClick={handleRefresh} className="!h-11 !rounded-xl !px-5 !border-border/70 !bg-surface-100 !text-text-main hover:!border-border hover:!bg-surface-200">
              Refresh
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateNew}
              className="!h-11 !rounded-xl !px-5 !font-semibold"
            >
              New Presentation
            </Button>
          </Space>
        </div>

        <div className="rounded-[2rem] border border-border/70 bg-surface-50 p-6 shadow-soft session-shell workbench-panel">
          <SessionList
            sessions={filteredSessions}
            loading={isLoading}
            onView={handleView}
            onDelete={handleDelete}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
          />
        </div>
      </div>
    </div>
  );
};
