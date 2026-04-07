/**
 * Files / Reference library page
 */

import { useState } from 'react';
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
import { getSessionDisplayTitle } from '../../components/chat/chatSessionTitle';
import { DEFAULT_PRESENTATION_TITLE } from '../../utils/constants';

const { Title, Text } = Typography;

export const FilesPage = () => {
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>();
  const [showUpload, setShowUpload] = useState(false);

  const { data: sessionsData } = useSessions();
  const sessions = sessionsData?.data || [];
  const activeSessions = sessions.filter((s) => s.status === SessionStatus.ACTIVE);
  const effectiveSelectedSessionId = selectedSessionId ?? activeSessions[0]?.id;
  const { data: filesData, isLoading, refetch } = useFiles({
    session_id: effectiveSelectedSessionId,
  });
  const deleteMutation = useDeleteFile();
  const downloadMutation = useDownloadFile();
  const createSessionMutation = useCreateSession();

  const files = filesData?.data || [];

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
      title: DEFAULT_PRESENTATION_TITLE,
      status: SessionStatus.ACTIVE,
      topic: 'Project for organizing reference materials',
    });
    setSelectedSessionId(result.id);
    setShowUpload(true);
  };

  const handleUploadComplete = () => {
    setShowUpload(false);
    refetch();
  };

  return (
    <div className="workbench-page h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-4 rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-6 shadow-soft workbench-panel lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-secondary">
              Reference workspace
            </div>
            <Title level={2} className="!m-0 !mt-3 !text-text-main">
              Reference Library
            </Title>
            <Text className="mt-2 block leading-7 !text-text-secondary">
              Organize PDFs, Word files, Markdown, and text references for the current project. These files will be used during presentation generation.
            </Text>
          </div>
          <Space wrap>
            <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
              Refresh
            </Button>
            {activeSessions.length === 0 ? (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateSession}>
                Create Project
              </Button>
            ) : (
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowUpload(!showUpload)}>
                {showUpload ? 'Hide Upload' : 'Upload References'}
              </Button>
            )}
          </Space>
        </div>

        {activeSessions.length === 0 ? (
          <Alert
            message="No active project yet"
            description="Create a presentation project first, then link reference files to it so the system knows where to use them."
            type="info"
            showIcon
            action={
              <Button size="small" type="primary" onClick={handleCreateSession}>
                Create Project
              </Button>
            }
          />
        ) : (
          <>
            <div className="rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-5 shadow-soft workbench-panel">
              <Space wrap className="!flex">
                <Text strong className="!text-text-main">
                  Current project:
                </Text>
                <Select
                  className="w-full sm:w-[320px]"
                  value={effectiveSelectedSessionId}
                  onChange={setSelectedSessionId}
                  options={activeSessions.map((session) => ({
                    label: getSessionDisplayTitle(session.title, session.topic),
                    value: session.id,
                  }))}
                />
              </Space>
            </div>

            {showUpload ? (
              <div className="rounded-[2rem] border border-border/70 bg-surface-50 p-5 shadow-soft workbench-panel">
                <FileUpload
                  sessionId={effectiveSelectedSessionId}
                  onUploadComplete={handleUploadComplete}
                />
              </div>
            ) : null}
          </>
        )}

        <div className="rounded-[2rem] border border-border/70 bg-surface-50 p-5 shadow-soft workbench-panel">
          {files.length === 0 && !isLoading ? (
            <Empty
              description={
                effectiveSelectedSessionId
                  ? 'No references have been uploaded for this project yet'
                  : 'Select a project to view its references'
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              {effectiveSelectedSessionId ? (
                <Button type="primary" onClick={() => setShowUpload(true)}>
                  Upload References
                </Button>
              ) : null}
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
    </div>
  );
};
