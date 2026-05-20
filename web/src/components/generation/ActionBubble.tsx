import { DownloadOutlined, FilePptOutlined, LoadingOutlined } from '@ant-design/icons';
import { Button, Progress, Select, message } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { slidegenApi } from '../../api/endpoints/slidegen';
import { useTemplates } from '../../hooks/useTemplates';
import { useSSE } from '../../hooks/useSSE';
import { useGenerationStore } from '../../store/generationStore';
import type { SSEEvent, ThemePreset } from '../../api/types/slidegen.types';

interface ActionBubbleProps {
  markdownContent: string;
  onGenerationStart?: () => void;
  onGenerationComplete?: (downloadUrl: string) => void;
  onError?: (error: string) => void;
}

const AUTO_THEME_PRESET = 'auto';
const INITIAL_PROGRESS_MESSAGE = 'Waiting for export to start...';

export const ActionBubble = ({
  markdownContent,
  onGenerationStart,
  onGenerationComplete,
  onError,
}: ActionBubbleProps) => {
  const [generating, setGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState(INITIAL_PROGRESS_MESSAGE);
  const [progressError, setProgressError] = useState<string | null>(null);
  const [selectedThemePreset, setSelectedThemePreset] = useState(AUTO_THEME_PRESET);
  const { template, setTemplate } = useGenerationStore();
  const { data: templates, isLoading: templatesLoading } = useTemplates();
  const { data: themePresets, isLoading: themesLoading } = useQuery<ThemePreset[]>({
    queryKey: ['theme-presets'],
    queryFn: slidegenApi.getThemePresets,
  });

  const templateOptions = useMemo(
    () =>
      (templates?.length ? templates : [{ id: 'general', name: 'General' }]).map((item) => ({
        label: item.name,
        value: item.id,
      })),
    [templates]
  );

  const themeOptions = useMemo(
    () => [
      { label: 'Auto Theme', value: AUTO_THEME_PRESET },
      ...(themePresets || []).map((item) => ({
        label: item.name,
        value: item.id,
      })),
    ],
    [themePresets]
  );

  const handleStreamMessage = useCallback(
    (event: SSEEvent) => {
      switch (event.event) {
        case 'step_started':
          setProgress((currentProgress) => Math.max(currentProgress, 3));
          setProgressMessage(event.message || event.step_name);
          break;
        case 'progress':
          setProgress(Math.round(event.progress));
          setProgressMessage(event.message || event.stage);
          break;
        case 'step_completed':
          setProgress((currentProgress) => Math.max(currentProgress, 95));
          setProgressMessage(event.message || event.step_name);
          break;
        case 'generation_completed':
          setProgress(100);
          setProgressMessage(event.message || 'Presentation is ready.');
          setProgressError(null);
          setDownloadUrl(event.download_url);
          setGenerating(false);
          onGenerationComplete?.(event.download_url);
          message.success('PPTX ready to download.');
          break;
        default:
          break;
      }
    },
    [onGenerationComplete]
  );

  const { connect } = useSSE({
    onMessage: handleStreamMessage,
    onError: (error) => {
      setGenerating(false);
      setProgressError(error.message);
      setProgressMessage('Generation failed.');
      onError?.(error.message);
    },
  });

  const handleGenerate = () => {
    if (!markdownContent.trim()) {
      const errorMessage = 'No markdown content available for PPTX generation.';
      message.error(errorMessage);
      onError?.(errorMessage);
      return;
    }

    setGenerating(true);
    setDownloadUrl(null);
    setProgress(0);
    setProgressError(null);
    setProgressMessage(INITIAL_PROGRESS_MESSAGE);
    onGenerationStart?.();

    connect(
      slidegenApi.getPPTXFromMarkdownStreamRequest({
        markdown_content: markdownContent,
        template,
        export_as: 'pptx',
        theme_preset: selectedThemePreset,
      })
    );
  };

  const handleDownload = () => {
    if (!downloadUrl) return;

    const anchor = document.createElement('a');
    anchor.href = downloadUrl;
    anchor.download = '';
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
  };

  return (
    <div className="flex flex-col gap-3 rounded-[1.75rem] border border-border/70 bg-surface-50 px-4 py-4 shadow-sm sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
      <div className="grid min-w-0 flex-1 grid-cols-1 gap-3 sm:grid-cols-[minmax(10rem,1fr)_minmax(10rem,1fr)]">
        <label className="min-w-0 space-y-1.5">
          <span className="block text-xs font-semibold uppercase tracking-[0.08em] text-text-muted">
            PPT template
          </span>
          <Select
            aria-label="Select template"
            value={template}
            options={templateOptions}
            loading={templatesLoading}
            disabled={generating}
            onChange={setTemplate}
            className="w-full"
          />
          <span className="block text-xs leading-5 text-text-muted">
            Choose the slide structure and base layout.
          </span>
        </label>
        <label className="min-w-0 space-y-1.5">
          <span className="block text-xs font-semibold uppercase tracking-[0.08em] text-text-muted">
            PPT theme
          </span>
          <Select
            aria-label="Select theme preset"
            value={selectedThemePreset}
            options={themeOptions}
            loading={themesLoading}
            disabled={generating}
            onChange={setSelectedThemePreset}
            className="w-full"
          />
          <span className="block text-xs leading-5 text-text-muted">
            Automatically match colors, typography, and accents to the content.
          </span>
        </label>
      </div>

      <Button
        type="primary"
        icon={
          generating ? <LoadingOutlined /> : downloadUrl ? <DownloadOutlined /> : <FilePptOutlined />
        }
        loading={generating}
        disabled={generating}
        onClick={downloadUrl ? handleDownload : () => void handleGenerate()}
        className="!h-10 !rounded-xl !px-4 !font-semibold"
      >
        {generating ? 'Generating...' : downloadUrl ? 'Download PPTX' : 'Generate PPTX'}
      </Button>

      {(generating || progress > 0 || progressError) && (
        <div className="w-full">
          <div className="mb-1 flex items-center justify-between gap-3 text-xs text-text-muted">
            <span className="truncate">{progressMessage}</span>
            <span className="shrink-0 tabular-nums">{progress}%</span>
          </div>
          <Progress
            percent={progress}
            size="small"
            showInfo={false}
            status={progressError ? 'exception' : generating ? 'active' : 'success'}
          />
          {progressError && <p className="mt-1 text-xs text-red-500">{progressError}</p>}
        </div>
      )}
    </div>
  );
};
