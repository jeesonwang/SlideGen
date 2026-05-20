/**
 * Streaming Progress Component for SSE
 */

import { useEffect, useState } from 'react';
import { Card, Progress, Timeline, Typography, Alert, Button, Space } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useSSE } from '../../hooks/useSSE';
import type { MarkdownStreamRequestConfig, SSEEvent } from '../../api/types/slidegen.types';

const { Title, Text, Paragraph } = Typography;

interface StreamingProgressProps {
  streamRequest: MarkdownStreamRequestConfig;
  onComplete: (content: string) => void;
  onError?: (error: Error) => void;
}

interface TimelineItem {
  status: 'process' | 'finish' | 'error' | 'wait';
  title: string;
  description?: string;
  timestamp: Date;
}

export const StreamingProgress: React.FC<StreamingProgressProps> = ({
  streamRequest,
  onComplete,
  onError,
}) => {
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('Initializing...');
  const [timelineItems, setTimelineItems] = useState<TimelineItem[]>([]);
  const [generatedContent, setGeneratedContent] = useState('');
  const [hasError, setHasError] = useState(false);

  const handleMessage = (event: SSEEvent) => {
    console.log('SSE Event:', event);

    switch (event.event) {
      case 'workflow_started':
        addTimelineItem('process', 'Workflow Started', event.message);
        setCurrentStage('Starting generation workflow...');
        setProgress(5);
        break;

      case 'step_started':
        if ('step_name' in event) {
          addTimelineItem('process', event.step_name, event.message ?? undefined);
          setCurrentStage(event.message || event.step_name);
          setProgress((prev) => Math.min(prev + 10, 90));
        }
        break;

      case 'step_completed':
        if ('step_name' in event) {
          addTimelineItem('finish', event.step_name, event.message ?? undefined);
          if (event.content) {
            setGeneratedContent((prev) => prev + '\n\n' + event.content);
          }
        }
        break;

      case 'loop_iteration_completed':
        if ('iteration' in event && 'total' in event) {
          const percentage = ((event.iteration + 1) / event.total) * 60 + 20;
          setProgress(Math.min(percentage, 90));
          addTimelineItem(
            'finish',
            `Section ${event.iteration + 1}/${event.total}`,
            (event.section_title || event.message) ?? undefined
          );
          if (event.content) {
            setGeneratedContent((prev) => prev + '\n\n' + event.content);
          }
        }
        break;

      case 'content_generated':
        if ('content' in event) {
          addTimelineItem('finish', 'Content Generated', event.message ?? undefined);
          setGeneratedContent((prev) => prev + '\n\n' + event.content);
        }
        break;

      case 'progress':
        if ('progress' in event) {
          setProgress(event.progress);
          setCurrentStage(event.message || event.stage);
        }
        break;

      case 'workflow_completed':
        addTimelineItem('finish', 'Workflow Completed', 'Generation finished successfully');
        setProgress(100);
        setCurrentStage('Complete!');
        if ('content' in event && event.content) {
          setGeneratedContent(event.content);
        }
        break;

      case 'workflow_error':
        if ('error' in event) {
          addTimelineItem('error', 'Error', event.error);
          setCurrentStage('Failed');
          setHasError(true);
        }
        break;
    }
  };

  const addTimelineItem = (
    status: TimelineItem['status'],
    title: string,
    description?: string
  ) => {
    setTimelineItems((prev) => [
      ...prev,
      {
        status,
        title,
        description,
        timestamp: new Date(),
      },
    ]);
  };

  const { connect, disconnect, isConnected, error } = useSSE({
    onMessage: handleMessage,
    onComplete,
    onError: (err) => {
      setHasError(true);
      onError?.(err);
    },
  });

  useEffect(() => {
    connect(streamRequest);

    return () => {
      disconnect();
    };
  }, [streamRequest, connect, disconnect]);

  const handleRetry = () => {
    setProgress(0);
    setCurrentStage('Initializing...');
    setTimelineItems([]);
    setGeneratedContent('');
    setHasError(false);
    connect(streamRequest);
  };

  const getTimelineIcon = (status: TimelineItem['status']) => {
    switch (status) {
      case 'process':
        return <LoadingOutlined />;
      case 'finish':
        return <CheckCircleOutlined className="text-green-500" />;
      case 'error':
        return <CloseCircleOutlined className="text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div>
      <Card>
        <Space direction="vertical" className="w-full" size="large">
          <div>
            <Title level={4}>
              {isConnected ? 'Generating Presentation...' : 'Connecting...'}
            </Title>
            <Text type="secondary">{currentStage}</Text>
          </div>

          <Progress
            percent={Math.round(progress)}
            status={hasError ? 'exception' : isConnected ? 'active' : 'normal'}
          />

          {hasError && error && (
            <Alert
              message="Generation Failed"
              description={error.message}
              type="error"
              showIcon
              action={
                <Button size="small" danger onClick={handleRetry}>
                  <ReloadOutlined /> Retry
                </Button>
              }
            />
          )}

          {timelineItems.length > 0 && (
            <div className="max-h-[300px] overflow-y-auto py-4">
              <Timeline
                items={timelineItems.map((item) => ({
                  dot: getTimelineIcon(item.status),
                  color: item.status === 'error' ? 'red' : item.status === 'finish' ? 'green' : 'blue',
                  children: (
                    <div>
                      <Text strong>{item.title}</Text>
                      {item.description && (
                        <div>
                          <Text type="secondary" className="text-xs">
                            {item.description}
                          </Text>
                        </div>
                      )}
                    </div>
                  ),
                }))}
              />
            </div>
          )}

          {generatedContent && (
            <div>
              <Text strong>Generated Content Preview:</Text>
              <Paragraph
                ellipsis={{ rows: 6, expandable: true, symbol: 'Show more' }}
                className="mt-2 rounded border border-border/70 bg-surface-100/80 p-3 whitespace-pre-wrap font-mono text-xs text-text-main"
              >
                {generatedContent}
              </Paragraph>
            </div>
          )}
        </Space>
      </Card>
    </div>
  );
};
