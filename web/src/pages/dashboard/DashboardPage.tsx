import { Button, List, Space, Tag, Typography } from 'antd';
import {
  ArrowRightOutlined,
  ClockCircleOutlined,
  FileAddOutlined,
  FolderOpenOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSessions } from '../../hooks/useSessions';
import { useFiles } from '../../hooks/useFiles';
import { useAuth } from '../../hooks/useAuth';
import { SessionStatus } from '../../api/types/session.types';
import { getSessionDisplayTitle } from '../../components/chat/chatSessionTitle';
import { getDashboardGreetingName } from './dashboardDisplay';
import { getSessionStatusPresentation } from '../../components/sessions/sessionPresentation';
import { useChatStore } from '../../store/chatStore';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Title, Text } = Typography;

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { setCurrentSession, loadMessages } = useChatStore();
  const { user } = useAuth();
  const greetingName = getDashboardGreetingName({
    username: user?.username,
    email: user?.email,
  });

  const { data: sessionsData } = useSessions({ limit: 10 });
  const { data: filesData } = useFiles();

  const visibleSessions =
    sessionsData?.data.filter(
      (session) =>
        session.status !== SessionStatus.DELETED &&
        session.status !== SessionStatus.ARCHIVED
    ) || [];

  const recentSessions = visibleSessions.slice(0, 5);
  const activeSessions = visibleSessions.filter((session) => session.status === SessionStatus.ACTIVE);
  const latestSession = activeSessions[0] || visibleSessions[0];
  const totalFiles = filesData?.count || 0;
  const openProject = (sessionId: string) => {
    setCurrentSession(sessionId);
    loadMessages(sessionId);
    navigate('/generate');
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-7 shadow-soft">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-text-secondary">
              Workbench Home
            </div>
            <Title level={2} className="!mb-3 !text-text-main">
              {greetingName}, pick up your presentation work from here
            </Title>
            <Text className="block max-w-2xl text-base leading-7 !text-text-secondary">
              Start with a clear topic, add your references, then shape the outline into a presentation you can export.
            </Text>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                size="large"
                onClick={() => navigate('/generate')}
                className="!h-12 !rounded-xl !px-5"
              >
                Start from a topic
              </Button>
              <Button
                icon={<FileAddOutlined />}
                size="large"
                onClick={() => navigate('/knowledge-base')}
                className="!h-12 !rounded-xl !border-border/70 !bg-surface-100 !px-5 !text-text-main"
              >
                Import references
              </Button>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-[1.75rem] border border-border/70 bg-surface-50 px-5 py-5">
              <div className="text-sm text-text-secondary">Projects</div>
              <div className="mt-2 text-3xl font-semibold text-text-main">{visibleSessions.length}</div>
            </div>
            <div className="rounded-[1.75rem] border border-border/70 bg-surface-50 px-5 py-5">
              <div className="text-sm text-text-secondary">In progress</div>
              <div className="mt-2 text-3xl font-semibold text-text-main">{activeSessions.length}</div>
            </div>
            <div className="rounded-[1.75rem] border border-border/70 bg-surface-50 px-5 py-5">
              <div className="text-sm text-text-secondary">References</div>
              <div className="mt-2 text-3xl font-semibold text-text-main">{totalFiles}</div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-6 shadow-soft">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-secondary">
                  Continue recent work
                </div>
                <Title level={4} className="!mb-0 !mt-2 !text-text-main">
                  {latestSession
                    ? getSessionDisplayTitle(latestSession.title, latestSession.topic)
                    : 'Create your first presentation'}
                </Title>
              </div>
              <ClockCircleOutlined className="text-lg text-primary-500" />
            </div>

            {latestSession ? (
              <>
                <Text className="block text-sm leading-6 !text-text-secondary">
                  {latestSession.topic?.trim() || 'Refine the structure, add supporting material, or regenerate the outline.'}
                </Text>
                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <Tag className="!rounded-full !border-border/70 !bg-surface-100 !px-3 !py-1 !text-text-secondary">
                    {dayjs(latestSession.update_time).fromNow()}
                  </Tag>
                  <Tag className="!rounded-full !border-border/70 !bg-surface-100 !px-3 !py-1 !text-text-secondary">
                    {latestSession.file_count} files
                  </Tag>
                  <Tag className="!rounded-full !border-border/70 !bg-surface-100 !px-3 !py-1 !text-text-secondary">
                    {latestSession.message_count} messages
                  </Tag>
                </div>
                <div className="mt-6">
                  <Button
                    type="primary"
                    icon={<ArrowRightOutlined />}
                    onClick={() => openProject(latestSession.id)}
                    className="!h-11 !rounded-xl !px-5"
                  >
                    Continue editing
                  </Button>
                </div>
              </>
            ) : (
              <div className="mt-4 rounded-[1.5rem] border border-dashed border-border px-5 py-6">
                <Text className="block text-sm leading-6 !text-text-secondary">
                  No projects yet. Create a presentation first, then add references and generate an outline.
                </Text>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/generate')}
                  className="!mt-4 !h-11 !rounded-xl !px-5"
                >
                  New Presentation
                </Button>
              </div>
            )}
          </div>

          <div className="rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-6 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-secondary">
                  Recently updated projects
                </div>
                <Title level={4} className="!mb-0 !mt-2 !text-text-main">
                  Keep your work moving
                </Title>
              </div>
              <Button
                type="link"
                onClick={() => navigate('/sessions')}
                className="!px-0 !text-primary-600"
              >
                View all projects
              </Button>
            </div>

            {recentSessions.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-border px-5 py-6">
                <Text className="block text-sm leading-6 !text-text-secondary">
                  No recent projects yet. Start from a topic or open the reference library to import existing material.
                </Text>
              </div>
            ) : (
              <List
                itemLayout="horizontal"
                dataSource={recentSessions}
                renderItem={(session) => {
                  const status = getSessionStatusPresentation(session.status);

                  return (
                    <List.Item className="!border-border/70 !px-0">
                      <div className="flex w-full flex-wrap items-center justify-between gap-4 rounded-[1.5rem] border border-border/70 bg-background px-4 py-4">
                        <div className="min-w-0 flex-1">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <Text strong className="!text-base !text-text-main">
                              {getSessionDisplayTitle(session.title, session.topic)}
                            </Text>
                            <Tag color={status.color} className="!rounded-full !px-3">
                              {status.label}
                            </Tag>
                          </div>
                          <Text className="block text-sm leading-6 !text-text-secondary">
                            {session.topic?.trim() || 'Open this project to continue shaping the outline and content structure.'}
                          </Text>
                          <Space size="middle" className="!mt-3">
                            <Text className="!text-xs !text-text-secondary">
                              {dayjs(session.update_time).fromNow()}
                            </Text>
                            <Text className="!text-xs !text-text-secondary">
                              {session.file_count} files
                            </Text>
                          </Space>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            onClick={() => openProject(session.id)}
                            className="!h-10 !rounded-xl !border-border/70 !bg-surface-100 !text-text-main"
                          >
                            Continue editing
                          </Button>
                          <Button
                            type="link"
                            icon={<FolderOpenOutlined />}
                            onClick={() => navigate('/knowledge-base')}
                            className="!px-0 !text-primary-600"
                          >
                            Open references
                          </Button>
                        </div>
                      </div>
                    </List.Item>
                  );
                }}
              />
            )}
          </div>
        </section>
      </div>
    </div>
  );
};
