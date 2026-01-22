/**
 * Dashboard Page with overview and quick actions
 */

import { Row, Col, Card, Statistic, Button, Typography, Space, List, Tag, Spin } from 'antd';
import {
  FileTextOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlusOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSessions } from '../../hooks/useSessions';
import { useFiles } from '../../hooks/useFiles';
import { useAuth } from '../../hooks/useAuth';
import { SessionStatus } from '../../api/types/session.types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Title, Text } = Typography;

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Fetch sessions and files for stats
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions({ limit: 10 });
  const { data: filesData, isLoading: filesLoading } = useFiles();

  // Calculate stats
  const totalSessions = sessionsData?.count || 0;
  const activeSessions = sessionsData?.data.filter(
    (s) => s.status === SessionStatus.ACTIVE
  ).length || 0;
  const completedSessions = sessionsData?.data.filter(
    (s) => s.status === SessionStatus.COMPLETED
  ).length || 0;
  const totalFiles = filesData?.count || 0;

  const recentSessions = sessionsData?.data.slice(0, 5) || [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case SessionStatus.ACTIVE:
        return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
      case SessionStatus.COMPLETED:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case SessionStatus.FAILED:
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case SessionStatus.ACTIVE:
        return 'processing';
      case SessionStatus.COMPLETED:
        return 'success';
      case SessionStatus.FAILED:
        return 'error';
      case SessionStatus.ARCHIVED:
        return 'default';
      default:
        return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="mb-8 animate-fade-in">
        <Title level={2} className="!mb-2 !font-heading !text-secondary-900">
          Welcome back, {user?.username || user?.email}! 👋
        </Title>
        <Text className="text-base text-secondary-600">
          Here's an overview of your presentation generation activity
        </Text>
      </div>

      {/* Stats Cards */}
      <Row gutter={[16, 16]} className="mb-6 animate-slide-up">
        <Col xs={24} sm={12} lg={6}>
          <Card className="modern-card border-0 hover:scale-105 transition-transform duration-200">
            <Statistic
              title={<span className="text-secondary-600 font-medium">Total Sessions</span>}
              value={totalSessions}
              prefix={<FileTextOutlined className="text-primary-600" />}
              loading={sessionsLoading}
              valueStyle={{ color: '#1E293B', fontWeight: 600, fontSize: 28 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="modern-card border-0 hover:scale-105 transition-transform duration-200">
            <Statistic
              title={<span className="text-secondary-600 font-medium">Active Sessions</span>}
              value={activeSessions}
              prefix={<ClockCircleOutlined className="text-accent-500" />}
              valueStyle={{ color: '#2563EB', fontWeight: 600, fontSize: 28 }}
              loading={sessionsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="modern-card border-0 hover:scale-105 transition-transform duration-200">
            <Statistic
              title={<span className="text-secondary-600 font-medium">Completed</span>}
              value={completedSessions}
              prefix={<CheckCircleOutlined className="text-success-500" />}
              valueStyle={{ color: '#16A34A', fontWeight: 600, fontSize: 28 }}
              loading={sessionsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="modern-card border-0 hover:scale-105 transition-transform duration-200">
            <Statistic
              title={<span className="text-secondary-600 font-medium">Knowledge Base</span>}
              value={totalFiles}
              prefix={<DatabaseOutlined className="text-primary-500" />}
              valueStyle={{ color: '#1E293B', fontWeight: 600, fontSize: 28 }}
              loading={filesLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Card
        title={<span className="text-lg font-heading font-semibold">Quick Actions</span>}
        className="modern-card border-0 mb-6"
      >
        <Space size="middle" wrap>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            size="large"
            onClick={() => navigate('/generate')}
            className="!h-12 !px-6 !rounded-lg !bg-primary-600 hover:!bg-primary-700 !font-medium !shadow-soft hover:!shadow-soft-lg transition-all duration-200"
          >
            Generate New Presentation
          </Button>
          <Button
            icon={<PlusOutlined />}
            size="large"
            onClick={() => navigate('/sessions')}
            className="!h-12 !px-6 !rounded-lg !font-medium hover:!shadow-soft transition-all duration-200"
          >
            View All Sessions
          </Button>
          <Button
            icon={<UploadOutlined />}
            size="large"
            onClick={() => navigate('/knowledge-base')}
            className="!h-12 !px-6 !rounded-lg !font-medium hover:!shadow-soft transition-all duration-200"
          >
            Upload Files
          </Button>
        </Space>
      </Card>

      {/* Recent Sessions */}
      <Card
        title={<span className="text-lg font-heading font-semibold">Recent Sessions</span>}
        className="modern-card border-0"
      >
        {sessionsLoading ? (
          <div className="text-center py-16">
            <Spin size="large" />
          </div>
        ) : recentSessions.length === 0 ? (
          <div className="text-center py-16">
            <div className="mb-4 inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-50">
              <ThunderboltOutlined className="text-3xl text-primary-600" />
            </div>
            <Text className="block text-base text-secondary-600 mb-4">
              No sessions yet. Create your first presentation!
            </Text>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              size="large"
              onClick={() => navigate('/generate')}
              className="!h-12 !px-6 !rounded-lg !bg-primary-600 hover:!bg-primary-700 !font-medium !shadow-soft hover:!shadow-soft-lg transition-all duration-200"
            >
              Get Started
            </Button>
          </div>
        ) : (
          <List
            itemLayout="horizontal"
            dataSource={recentSessions}
            renderItem={(session) => (
              <List.Item
                actions={[
                  <Button
                    type="link"
                    onClick={() => navigate(`/sessions`)}
                    key="view"
                    className="!text-primary-600 hover:!text-primary-700 !font-medium"
                  >
                    View
                  </Button>,
                ]}
                className="!px-4 hover:bg-secondary-50 rounded-lg transition-colors duration-200"
              >
                <List.Item.Meta
                  avatar={
                    <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-secondary-100">
                      {getStatusIcon(session.status)}
                    </div>
                  }
                  title={
                    <Space>
                      <Text strong className="text-secondary-900">{session.title}</Text>
                      <Tag
                        color={getStatusColor(session.status)}
                        className="!rounded-md !px-2"
                      >
                        {session.status}
                      </Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={0}>
                      {session.topic && (
                        <Text className="text-secondary-600" ellipsis>
                          {session.topic}
                        </Text>
                      )}
                      <Text className="text-xs text-secondary-500">
                        {dayjs(session.create_time).fromNow()} • {session.file_count}{' '}
                        files • {session.message_count} messages
                      </Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
};
