/**
 * PPT Generation Page
 */

import { useState, useEffect } from 'react';
import { Typography, Select, Button, Space, Alert } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { GenerationWizard } from '../../components/generation/GenerationWizard';
import { useSessions, useCreateSession } from '../../hooks/useSessions';
import { SessionStatus } from '../../api/types/session.types';

const { Title, Text } = Typography;

export const GenerationPage = () => {
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>();

  const { data: sessionsData } = useSessions();
  const createSessionMutation = useCreateSession();

  const sessions = sessionsData?.data || [];
  const activeSessions = sessions.filter((s) => s.status === SessionStatus.ACTIVE);

  // Auto-select first active session if available
  useEffect(() => {
    if (!selectedSessionId && activeSessions.length > 0) {
      setSelectedSessionId(activeSessions[0].id);
    }
  }, [activeSessions, selectedSessionId]);

  const handleCreateSession = async () => {
    const result = await createSessionMutation.mutateAsync({
      title: `Presentation ${new Date().toLocaleDateString()}`,
      status: SessionStatus.ACTIVE,
      topic: 'New presentation generation',
    });
    setSelectedSessionId(result.id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <Title level={2} className="!mb-2 !font-heading !text-secondary-900">
          Generate Presentation
        </Title>
        <Text className="text-base text-secondary-600">
          Create AI-powered presentations with streaming generation
        </Text>
      </div>

      {activeSessions.length === 0 ? (
        <Alert
          message="No Active Session"
          description="You need to create an active session before generating presentations."
          type="info"
          showIcon
          className="!rounded-lg !border-primary-200 !bg-primary-50"
          action={
            <Button
              size="large"
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateSession}
              loading={createSessionMutation.isPending}
              className="!h-10 !px-4 !rounded-lg !bg-primary-600 hover:!bg-primary-700 !font-medium !shadow-soft hover:!shadow-soft-lg transition-all duration-200"
            >
              Create Session
            </Button>
          }
        />
      ) : (
        <>
          <div className="modern-card p-6 border-0 mb-6 animate-slide-up">
            <Space size="middle" className="w-full flex-wrap">
              <div className="flex items-center gap-3">
                <Text strong className="text-secondary-700 text-base">Session:</Text>
                <Select
                  className="w-[300px]"
                  size="large"
                  value={selectedSessionId}
                  onChange={setSelectedSessionId}
                  options={activeSessions.map((session) => ({
                    label: session.title,
                    value: session.id,
                  }))}
                />
              </div>
              <Button
                icon={<PlusOutlined />}
                size="large"
                onClick={handleCreateSession}
                loading={createSessionMutation.isPending}
                className="!h-11 !px-6 !rounded-lg !font-medium hover:!shadow-soft transition-all duration-200"
              >
                New Session
              </Button>
            </Space>
          </div>

          {selectedSessionId && (
            <div className="animate-fade-in">
              <GenerationWizard sessionId={selectedSessionId} />
            </div>
          )}
        </>
      )}
    </div>
  );
};
