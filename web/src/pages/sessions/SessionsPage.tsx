/**
 * Sessions Management Page
 */

import { useState, useMemo } from 'react';
import { Typography, Button, Space } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { SessionList } from '../../components/sessions/SessionList';
import {
  useSessions,
  useDeleteSession,
  useArchiveSession,
} from '../../hooks/useSessions';
import type { SessionPublic } from '../../api/types/session.types';

const { Title, Text } = Typography;

export const SessionsPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const { data: sessionsData, isLoading, refetch } = useSessions();
  const deleteMutation = useDeleteSession();
  const archiveMutation = useArchiveSession();

  const sessions = sessionsData?.data || [];

  // Filter sessions by search term
  const filteredSessions = useMemo(() => {
    if (!searchTerm) return sessions;

    const lowerSearch = searchTerm.toLowerCase();
    return sessions.filter(
      (session) =>
        session.title.toLowerCase().includes(lowerSearch) ||
        session.topic?.toLowerCase().includes(lowerSearch)
    );
  }, [sessions, searchTerm]);

  const handleView = (session: SessionPublic) => {
    // For now, just show an alert
    // In the future, this could navigate to a detail view
    console.log('View session:', session);
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  const handleArchive = async (id: string) => {
    await archiveMutation.mutateAsync(id);
  };

  const handleCreateNew = () => {
    navigate('/generate');
  };

  const handleRefresh = () => {
    refetch();
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
            Sessions
          </Title>
          <Text type="secondary">
            Manage your presentation generation sessions
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            Refresh
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateNew}
          >
            New Session
          </Button>
        </Space>
      </div>

      <SessionList
        sessions={filteredSessions}
        loading={isLoading}
        onView={handleView}
        onDelete={handleDelete}
        onArchive={handleArchive}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />
    </div>
  );
};
