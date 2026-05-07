import type { ChangeEvent, RefObject } from 'react';
import {
  FileAddOutlined,
  FileTextOutlined,
  LoadingOutlined,
  RobotOutlined,
  SendOutlined,
} from '@ant-design/icons';
import { Button, Input } from 'antd';
import type { FileMetadataPublic } from '../../api/types/file.types';
import { ConfigurationPanel } from '../config/ConfigurationPanel';

const { TextArea } = Input;

interface ComposerCardProps {
  input: string;
  isStreaming: boolean;
  hasMessages: boolean;
  selectedReferenceFiles: FileMetadataPublic[];
  fileInputRef: RefObject<HTMLInputElement | null>;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onGenerate: () => void;
  onOpenFilePicker: () => void;
  onInlineUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  onRemoveReferenceFile: (fileId: string) => void;
}

export const ComposerCard = ({
  input,
  isStreaming,
  hasMessages,
  selectedReferenceFiles,
  fileInputRef,
  onInputChange,
  onSend,
  onGenerate,
  onOpenFilePicker,
  onInlineUpload,
  onRemoveReferenceFile,
}: ComposerCardProps) => (
  <div className="mx-auto max-w-5xl">
    <div className="workbench-tip-panel mb-5 flex items-start gap-3 rounded-[1.6rem] px-4 py-4 sm:px-5">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-brand-surface text-brand-strong">
        <RobotOutlined className="text-lg" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[0.95rem] font-semibold text-text-main">
          Tip: shape the structure first, then refine the slides
        </div>
        <p className="mt-1 text-sm leading-6 text-text-secondary">
          Describe the topic, the audience, and the outcome you want. Upload references when you
          want the outline grounded in source material.
        </p>
      </div>
    </div>

    <div className="mb-8 flex flex-col gap-4 rounded-[2rem] border border-border/70 bg-background px-4 py-4 shadow-soft sm:px-5 workbench-stage-panel">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt,.md"
        multiple
        hidden
        onChange={onInlineUpload}
      />

      <div className="flex flex-wrap gap-2">
        {selectedReferenceFiles.length > 0 ? (
          selectedReferenceFiles.map((file) => (
            <div
              key={file.id}
              className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-surface-100 px-3 py-2 text-xs text-text-main"
            >
              <FileTextOutlined className="text-text-secondary" />
              <span className="max-w-40 truncate">{file.filename}</span>
              <button
                type="button"
                onClick={() => onRemoveReferenceFile(file.id)}
                className="border-0 bg-transparent p-0 text-text-secondary transition-colors hover:text-red-500"
                aria-label={`Remove reference ${file.filename}`}
              >
                ×
              </button>
            </div>
          ))
        ) : (
          <div className="rounded-full border border-dashed border-border/70 px-3 py-2 text-xs text-text-secondary">
            Linked references appear here and are automatically used during generation.
          </div>
        )}
      </div>

      <TextArea
        aria-label="Presentation prompt"
        placeholder="Describe the topic, audience, key message, or structure requirements. Example: Create a 10-slide university admissions deck that highlights academic strengths, career outcomes, and campus life."
        autoSize={{ minRows: 2, maxRows: 7 }}
        value={input}
        onChange={(event) => onInputChange(event.target.value)}
        onPressEnter={(event) => {
          if (!event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
        disabled={isStreaming}
        className="!border-none !bg-transparent !px-2 !py-3 !text-base !leading-8 !text-text-main !shadow-none placeholder:!text-text-muted"
      />

      <div className="flex flex-col gap-3 border-t border-border/70 pt-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="text"
            icon={<FileAddOutlined />}
            onClick={onOpenFilePicker}
            aria-label="Upload reference files"
            className="!h-11 !rounded-xl !px-4 !text-text-secondary hover:!bg-surface-100 hover:!text-text-main"
          >
            Upload references
          </Button>

          <Button
            type="link"
            onClick={onGenerate}
            disabled={isStreaming || !hasMessages}
            className="!h-11 !px-2 !text-xs !font-semibold !text-primary-600 disabled:!text-text-muted"
          >
            Regenerate outline
          </Button>
        </div>

        <Button
          type="primary"
          icon={isStreaming ? <LoadingOutlined /> : <SendOutlined />}
          onClick={onSend}
          disabled={!input.trim() || isStreaming}
          aria-label="Send prompt"
          className="!h-12 !rounded-2xl !px-6 !font-semibold"
        >
          Generate Outline
        </Button>
      </div>

      <div className="border-t border-border/70 pt-3.5">
        <ConfigurationPanel />
      </div>
    </div>
  </div>
);
