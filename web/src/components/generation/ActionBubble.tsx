import { DownloadOutlined, FilePptOutlined, LoadingOutlined } from '@ant-design/icons';
import { Button, Select, message } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { slidegenApi } from '../../api/endpoints/slidegen';
import { useTemplates } from '../../hooks/useTemplates';
import { useGenerationStore } from '../../store/generationStore';
import type { ThemePreset } from '../../api/types/slidegen.types';

interface ActionBubbleProps {
  markdownContent: string;
  onGenerationStart?: () => void;
  onGenerationComplete?: (downloadUrl: string) => void;
  onError?: (error: string) => void;
}

const DEFAULT_THEME_VALUE = '__default_theme__';

export const ActionBubble = ({
  markdownContent,
  onGenerationStart,
  onGenerationComplete,
  onError,
}: ActionBubbleProps) => {
  const [generating, setGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [selectedThemePreset, setSelectedThemePreset] = useState<string | null>(null);
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
      { label: 'Default theme', value: DEFAULT_THEME_VALUE },
      ...(themePresets || []).map((item) => ({
        label: item.name,
        value: item.id,
      })),
    ],
    [themePresets]
  );

  const handleGenerate = async () => {
    if (!markdownContent.trim()) {
      const errorMessage = 'No markdown content available for PPTX generation.';
      message.error(errorMessage);
      onError?.(errorMessage);
      return;
    }

    setGenerating(true);
    setDownloadUrl(null);
    onGenerationStart?.();

    try {
      const response = await slidegenApi.generatePPTXFromMarkdown({
        markdown_content: markdownContent,
        template,
        export_as: 'pptx',
        theme_preset: selectedThemePreset,
      });

      if (!response.success || !response.result?.download_url) {
        const errorMessage = response.error || response.message || 'PPTX generation failed.';
        message.error(errorMessage);
        onError?.(errorMessage);
        return;
      }

      setDownloadUrl(response.result.download_url);
      onGenerationComplete?.(response.result.download_url);
      message.success('PPTX ready to download.');
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'PPTX generation failed. Please try again.';
      message.error(errorMessage);
      onError?.(errorMessage);
    } finally {
      setGenerating(false);
    }
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
    <div className="-mt-1 flex flex-col gap-3 rounded-b-[28px] border-x border-b border-border/70 bg-surface-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="grid min-w-0 flex-1 grid-cols-1 gap-2 sm:grid-cols-[minmax(10rem,1fr)_minmax(10rem,1fr)]">
        <Select
          aria-label="Select template"
          value={template}
          options={templateOptions}
          loading={templatesLoading}
          onChange={setTemplate}
          className="w-full"
        />
        <Select
          aria-label="Select theme preset"
          value={selectedThemePreset ?? DEFAULT_THEME_VALUE}
          options={themeOptions}
          loading={themesLoading}
          onChange={(value) =>
            setSelectedThemePreset(value === DEFAULT_THEME_VALUE ? null : value)
          }
          className="w-full"
        />
      </div>

      <Button
        type="primary"
        icon={
          generating ? <LoadingOutlined /> : downloadUrl ? <DownloadOutlined /> : <FilePptOutlined />
        }
        loading={generating}
        onClick={downloadUrl ? handleDownload : () => void handleGenerate()}
        className="!h-10 !rounded-xl !px-4 !font-semibold"
      >
        {generating ? 'Generating...' : downloadUrl ? 'Download PPTX' : 'Generate PPTX'}
      </Button>
    </div>
  );
};
