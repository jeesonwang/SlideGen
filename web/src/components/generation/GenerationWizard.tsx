/**
 * PPT Generation Wizard Component
 */

import { useState, useEffect } from 'react';
import { Steps, Button, Form, message } from 'antd';
import { TopicInput } from './TopicInput';
import { StreamingProgress } from './StreamingProgress';
import { MarkdownEditor } from './MarkdownEditor';
import { OutlineEditor } from './OutlineEditor';
import { useGenerationStore } from '../../store/generationStore';
import { slidegenApi } from '../../api/endpoints/slidegen';
import { useAuthStore } from '../../store/authStore';
import { GENERATION_DEFAULTS } from '../../utils/constants';
import { cn } from '../../utils/classnames';
import type { GenerateMarkdownRequest } from '../../api/types/slidegen.types';
import type { MarkdownStreamRequestConfig } from '../../api/types/slidegen.types';
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
    generationParams,
    reset,
  } = useGenerationStore();

  const [streamRequest, setStreamRequest] = useState<MarkdownStreamRequestConfig | null>(null);
  const [exporting, setExporting] = useState(false);
  const [viewMode, setViewMode] = useState<'outline' | 'markdown'>('outline');

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

      const params: GenerateMarkdownRequest = {
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
        template: values.template || GENERATION_DEFAULTS.TEMPLATE,
      };

      setGenerationParams(params);

      // Get the SSE stream URL
      const request = slidegenApi.getMarkdownStreamRequest(params);
      setStreamRequest(request);

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
        template: generationParams?.template || GENERATION_DEFAULTS.TEMPLATE,
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
    setViewMode('outline');
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
      title: 'Edit & Preview',
      description: 'Review and download PPTX',
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
        className={cn("mb-8")}
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
            template: GENERATION_DEFAULTS.TEMPLATE,
          }}
        >
          <TopicInput sessionId={sessionId} />

          <div className={cn("mt-6 text-right")}>
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

      {currentStep === 'generating' && streamRequest && (
        <div>
          <StreamingProgress
            streamRequest={streamRequest}
            onComplete={handleGenerationComplete}
            onError={handleGenerationError}
          />

          <div className={cn("mt-6 text-right")}>
            <Button onClick={handleBack}>Back</Button>
          </div>
        </div>
      )}

      {currentStep === 'editing' && (
        <div className={cn("animate-fade-in")}>
          <div className={cn("flex justify-between items-center mb-6")}>
             <div className={cn("space-y-1")}>
                <h2 className={cn("text-2xl font-bold text-text-main")}>
                    {viewMode === 'outline' ? 'Generate Outline' : 'Edit Markdown'}
                </h2>
                <p className={cn("text-text-secondary")}>
                    {viewMode === 'outline'
                        ? 'Review and edit your presentation structure below.'
                        : 'Fine-tune the markdown content directly.'}
                </p>
             </div>
             <div className={cn("flex gap-3")}>
                <Button
                    onClick={() => setViewMode('outline')}
                    type={viewMode === 'outline' ? 'primary' : 'default'}
                >
                    Outline View
                </Button>
                <Button
                    onClick={() => setViewMode('markdown')}
                    type={viewMode === 'markdown' ? 'primary' : 'default'}
                >
                    Markdown View
                </Button>
             </div>
          </div>

          {viewMode === 'outline' ? (
             <div className={cn("mb-8")}>
                <OutlineEditor
                    value={markdownContent}
                    onChange={handleMarkdownChange}
                />

                <div className={cn(
                  "mt-8 flex justify-end gap-3 sticky bottom-0",
                  "bg-surface-50/85 backdrop-blur p-4",
                  "border-t border-border/70 shadow-lg -mx-4 px-8"
                )}>
                     <Button size="large" onClick={handleReset}>
                        Start New
                     </Button>
                     <Button
                        type="primary"
                        size="large"
                        onClick={handleExportPPTX}
                        loading={exporting}
                     >
                        Export Presentation
                     </Button>
                </div>
             </div>
          ) : (
            <div>
              <MarkdownEditor
                value={markdownContent}
                onChange={handleMarkdownChange}
                onExport={handleExportPPTX}
                exporting={exporting}
              />

              <div className={cn("mt-6 text-right")}>
                <Button onClick={handleReset} className={cn("mr-2")}>
                  Start New Generation
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
