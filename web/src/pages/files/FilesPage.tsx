/**
 * Files / Knowledge Base Management Page
 */

import { useState, useEffect } from 'react';
import { Typography, Button, Space, Select, Alert, Empty } from 'antd';
import { ReloadOutlined, PlusOutlined } from '@ant-design/icons';
import { FileUpload } from '../../components/files/FileUpload';
import { FileList } from '../../components/files/FileList';
import {
  useFiles,
  useDeleteFile,
  useDownloadFile,
} from '../../hooks/useFiles';
import { useSessions, useCreateSession } from '../../hooks/useSessions';
import { SessionStatus } from '../../api/types/session.types';
import type { FileMetadataPublic } from '../../api/types/file.types';

const { Title, Text } = Typography;

export const FilesPage = () => {
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>();
  const [showUpload, setShowUpload] = useState(false);

  const { data: sessionsData } = useSessions();
  const { data: filesData, isLoading, refetch } = useFiles({
    session_id: selectedSessionId,
  });
  const deleteMutation = useDeleteFile();
  const downloadMutation = useDownloadFile();
  const createSessionMutation = useCreateSession();

  const files = filesData?.data || [];
  const sessions = sessionsData?.data || [];
  const activeSessions = sessions.filter((s) => s.status === SessionStatus.ACTIVE);

  // Auto-select first active session if available
  useEffect(() => {
    if (!selectedSessionId && activeSessions.length > 0) {
      setSelectedSessionId(activeSessions[0].id);
    }
  }, [activeSessions, selectedSessionId]);

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  const handleDownload = async (file: FileMetadataPublic) => {
    await downloadMutation.mutateAsync({
      id: file.id,
      filename: file.filename,
    });
  };

  const handleRefresh = () => {
    refetch();
  };

  const handleCreateSession = async () => {
    const result = await createSessionMutation.mutateAsync({
      title: 'Knowledge Base Session',
      status: SessionStatus.ACTIVE,
      topic: 'File uploads for knowledge base',
    });
    setSelectedSessionId(result.id);
    setShowUpload(true);
  };

  const handleUploadComplete = () => {
    setShowUpload(false);
    refetch();
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={2} className="!m-0">
            Knowledge Base
          </Title>
          <Text type="secondary">
            Upload and manage files for presentation generation
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            Refresh
          </Button>
          {activeSessions.length === 0 ? (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateSession}
            >
              Create Session
            </Button>
          ) : (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setShowUpload(!showUpload)}
            >
              {showUpload ? 'Hide Upload' : 'Upload Files'}
            </Button>
          )}
        </Space>
      </div>

      {activeSessions.length === 0 ? (
        <Alert
          message="No Active Session"
          description="You need to create an active session before uploading files."
          type="info"
          showIcon
          action={
            <Button size="small" type="primary" onClick={handleCreateSession}>
              Create Session
            </Button>
          }
        />
      ) : (
        <>
          <div className="mb-6">
            <Space>
              <Text strong>Session:</Text>
              <Select
                className="w-[300px]"
                value={selectedSessionId}
                onChange={setSelectedSessionId}
                options={activeSessions.map((session) => ({
                  label: session.title,
                  value: session.id,
                }))}
              />
            </Space>
          </div>

          {showUpload && (
            <div className="mb-6">
              <FileUpload
                sessionId={selectedSessionId}
                onUploadComplete={handleUploadComplete}
              />
            </div>
          )}
        </>
      )}

      <div className="mt-6">
        {files.length === 0 && !isLoading ? (
          <Empty
            description={
              selectedSessionId
                ? 'No files uploaded yet'
                : 'Select a session to view files'
            }
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            {selectedSessionId && (
              <Button
                type="primary"
                onClick={() => setShowUpload(true)}
              >
                Upload Files
              </Button>
            )}
          </Empty>
        ) : (
          <FileList
            files={files}
            loading={isLoading}
            onDelete={handleDelete}
            onDownload={handleDownload}
          />
        )}
      </div>
    </div>
  );
};
