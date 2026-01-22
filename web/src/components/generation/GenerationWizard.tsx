/**
 * PPT Generation Wizard Component
 */

import { useState, useEffect, useMemo } from 'react';
import { Steps, Button, Form, message } from 'antd';
import { TopicInput } from './TopicInput';
import { StreamingProgress } from './StreamingProgress';
import { MarkdownEditor } from './MarkdownEditor';
import { useGenerationStore } from '../../store/generationStore';
import { slidegenApi } from '../../api/endpoints/slidegen';
import { useAuthStore } from '../../store/authStore';
import { GENERATION_DEFAULTS } from '../../utils/constants';
import type { GenerateMarkdownRequest } from '../../api/types/slidegen.types';
import { Tone, Verbosity } from '../../api/types/slidegen.types';

interface GenerationWizardProps {
  sessionId?: string;
}

export const GenerationWizard: React.FC<GenerationWizardProps> = ({
  sessionId,
}) => {
  const [form] = Form.useForm();
  const { user } = useAuthStore();
  const {
    currentStep,
    setStep,
    markdownContent,
    setMarkdownContent,
    setGenerationParams,
    reset,
  } = useGenerationStore();

  const [streamUrl, setStreamUrl] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    // Reset on mount
    reset();
  }, [reset]);

  const handleStartGeneration = async () => {
    try {
      const values = await form.validateFields();

      if (!user?.id) {
        message.error('User not authenticated');
        return;
      }

      const params: GenerateMarkdownRequest = useMemo(
        () => ({
          content: values.content,
          instructions: values.instructions || undefined,
          tone: values.tone || Tone.DEFAULT,
          verbosity: values.verbosity || Verbosity.STANDARD,
          web_search: values.web_search || false,
          n_slides: values.n_slides || GENERATION_DEFAULTS.N_SLIDES,
          language: values.language || GENERATION_DEFAULTS.LANGUAGE,
          files: values.files || undefined,
          user_id: user.id,
          llm_config_id: values.llm_config_id || undefined,
          embedding_config_id: values.embedding_config_id || undefined,
          session_id: sessionId || undefined,
        }),
        [
          values.content,
          values.instructions,
          values.tone,
          values.verbosity,
          values.web_search,
          values.n_slides,
          values.language,
          values.files,
          user.id,
          values.llm_config_id,
          values.embedding_config_id,
          sessionId,
        ]
      );

      setGenerationParams(params);

      // Get the SSE stream URL
      const url = slidegenApi.getMarkdownStreamURL(params);
      setStreamUrl(url);

      // Move to streaming step
      setStep('generating');
    } catch (error) {
      console.error('Form validation failed:', error);
    }
  };

  const handleGenerationComplete = (content: string) => {
    setMarkdownContent(content);
    setStep('editing');
    message.success('Markdown generation completed!');
  };

  const handleGenerationError = (error: Error) => {
    message.error(`Generation failed: ${error.message}`);
  };

  const handleMarkdownChange = (content: string) => {
    setMarkdownContent(content);
  };

  const handleExportPPTX = async () => {
    if (!markdownContent) {
      message.error('No markdown content to export');
      return;
    }

    setExporting(true);
    try {
      const result = await slidegenApi.generatePPTXFromMarkdown({
        markdown_content: markdownContent,
        template: GENERATION_DEFAULTS.TEMPLATE,
        export_as: GENERATION_DEFAULTS.EXPORT_AS,
      });

      message.success('PPTX generation started!');

      // Download the file
      if (result.download_url) {
        const link = document.createElement('a');
        link.href = result.download_url;
        link.download = 'presentation.pptx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        message.success('Presentation downloaded successfully!');
      } else if (result.task_id) {
        // If it's an async task, download using task_id
        const blob = await slidegenApi.downloadPPTX(result.task_id);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'presentation.pptx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        message.success('Presentation downloaded successfully!');
      }
    } catch (error: any) {
      message.error(error?.detail || 'Failed to generate PPTX');
    } finally {
      setExporting(false);
    }
  };

  const handleReset = () => {
    reset();
    form.resetFields();
  };

  const handleBack = () => {
    if (currentStep === 'generating') {
      setStep('configure');
    } else if (currentStep === 'editing') {
      setStep('generating');
    }
  };

  const steps = [
    {
      title: 'Configure',
      description: 'Set up generation parameters',
    },
    {
      title: 'Generate',
      description: 'AI creates markdown content',
    },
    {
      title: 'Edit & Export',
      description: 'Review and export PPTX',
    },
  ];

  const getCurrentStepIndex = () => {
    switch (currentStep) {
      case 'configure':
        return 0;
      case 'generating':
        return 1;
      case 'editing':
        return 2;
      default:
        return 0;
    }
  };

  return (
    <div>
      <Steps
        current={getCurrentStepIndex()}
        items={steps}
        className="mb-8"
      />

      {currentStep === 'configure' && (
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            tone: GENERATION_DEFAULTS.TONE,
            verbosity: GENERATION_DEFAULTS.VERBOSITY,
            n_slides: GENERATION_DEFAULTS.N_SLIDES,
            language: GENERATION_DEFAULTS.LANGUAGE,
            web_search: GENERATION_DEFAULTS.WEB_SEARCH,
            include_title_slide: GENERATION_DEFAULTS.INCLUDE_TITLE_SLIDE,
            include_table_of_contents: GENERATION_DEFAULTS.INCLUDE_TOC,
          }}
        >
          <TopicInput sessionId={sessionId} />

          <div className="mt-6 text-right">
            <Button
              type="primary"
              size="large"
              onClick={handleStartGeneration}
            >
              Start Generation
            </Button>
          </div>
        </Form>
      )}

      {currentStep === 'generating' && streamUrl && (
        <div>
          <StreamingProgress
            streamUrl={streamUrl}
            onComplete={handleGenerationComplete}
            onError={handleGenerationError}
          />

          <div className="mt-6 text-right">
            <Button onClick={handleBack}>Back</Button>
          </div>
        </div>
      )}

      {currentStep === 'editing' && (
        <div>
          <MarkdownEditor
            value={markdownContent}
            onChange={handleMarkdownChange}
            onExport={handleExportPPTX}
            exporting={exporting}
          />

          <div className="mt-6 text-right">
            <Button onClick={handleReset} className="mr-2">
              Start New Generation
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
