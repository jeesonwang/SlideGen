/**
 * Markdown Editor Component
 */

import { useState, useMemo } from 'react';
import { Card, Typography, Tabs, Input, Button, Space } from 'antd';
import { EyeOutlined, EditOutlined, CopyOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import type { Components, ExtraProps } from 'react-markdown';
import type { ComponentPropsWithoutRef } from 'react';

const { TextArea } = Input;
const { Title } = Typography;

type MarkdownHeadingProps<Tag extends 'h1' | 'h2' | 'h3' | 'h4' | 'ul' | 'ol'> =
  ComponentPropsWithoutRef<Tag> & ExtraProps;
type MarkdownCodeProps = ComponentPropsWithoutRef<'code'> & ExtraProps & {
  inline?: boolean;
};

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExport: () => void;
  exporting?: boolean;
}

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  onExport,
  exporting = false,
}) => {
  const [activeTab, setActiveTab] = useState<'edit' | 'preview'>('preview');

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
  };

  const markdownComponents = useMemo<Components>(
    () => ({
      h1: (props: MarkdownHeadingProps<'h1'>) => (
        <h1 className="border-b-2 border-primary-500 pb-2 text-primary-500" {...props} />
      ),
      h2: (props: MarkdownHeadingProps<'h2'>) => (
        <h2 className="mt-6 text-primary-500" {...props} />
      ),
      h3: (props: MarkdownHeadingProps<'h3'>) => (
        <h3 className="text-primary-400" {...props} />
      ),
      h4: (props: MarkdownHeadingProps<'h4'>) => (
        <h4 className="font-semibold text-text-main" {...props} />
      ),
      ul: (props: MarkdownHeadingProps<'ul'>) => (
        <ul className="leading-relaxed" {...props} />
      ),
      ol: (props: MarkdownHeadingProps<'ol'>) => (
        <ol className="leading-relaxed" {...props} />
      ),
      code: ({ inline, ...props }: MarkdownCodeProps) =>
        inline ? (
          <code
            className="rounded bg-surface-100 px-1.5 py-0.5 font-mono text-text-main"
            {...props}
          />
        ) : (
          <code
            className="block overflow-x-auto rounded bg-surface-100 p-3 font-mono text-text-main"
            {...props}
          />
        ),
    }),
    []
  );

  return (
    <Card>
      <Space direction="vertical" className="w-full" size="large">
        <div className="flex justify-between items-center">
          <Title level={4}>Edit Markdown Content</Title>
          <Space>
            <Button icon={<CopyOutlined />} onClick={handleCopy}>
              Copy
            </Button>
            <Button
              type="primary"
              onClick={onExport}
              loading={exporting}
              size="large"
            >
              Generate & Download PPTX
            </Button>
          </Space>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as 'edit' | 'preview')}
          items={[
            {
              key: 'preview',
              label: (
                <span>
                  <EyeOutlined /> Preview
                </span>
              ),
              children: (
                <div className="min-h-[400px] max-h-[600px] overflow-y-auto rounded border border-border/70 bg-surface-50 p-4 text-text-main">
                  <ReactMarkdown components={markdownComponents}>
                    {value}
                  </ReactMarkdown>
                </div>
              ),
            },
            {
              key: 'edit',
              label: (
                <span>
                  <EditOutlined /> Edit
                </span>
              ),
              children: (
                <TextArea
                  value={value}
                  onChange={(e) => onChange(e.target.value)}
                  className="min-h-[400px] max-h-[600px] font-mono text-sm"
                  placeholder="Edit your markdown content here..."
                />
              ),
            },
          ]}
        />

        <div className="rounded border border-primary-500/20 bg-primary-500/10 p-3">
          <Typography.Text className="text-xs">
            <strong>Tip:</strong> Use # for the deck title, ## for chapters, ### for slides, and #### for topics.
          </Typography.Text>
        </div>
      </Space>
    </Card>
  );
};
