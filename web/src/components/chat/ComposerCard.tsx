import { memo, type ChangeEvent, type RefObject } from 'react';
import {
  FileAddOutlined,
  FileTextOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { Input } from 'antd';
import type { FileMetadataPublic } from '../../api/types/file.types';
import { ConfigurationPanel } from '../config/ConfigurationPanel';

const { TextArea } = Input;

interface ComposerCardProps {
  input: string;
  isStreaming: boolean;
  selectedReferenceFiles: FileMetadataPublic[];
  fileInputRef: RefObject<HTMLInputElement | null>;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onOpenFilePicker: () => void;
  onInlineUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  onRemoveReferenceFile: (fileId: string) => void;
}

export const ComposerCard = memo(({
  input,
  isStreaming,
  selectedReferenceFiles,
  fileInputRef,
  onInputChange,
  onSend,
  onOpenFilePicker,
  onInlineUpload,
  onRemoveReferenceFile,
}: ComposerCardProps) => (
  <div className="mx-auto max-w-5xl">
    <div className="mb-8 flex flex-col gap-4 rounded-[2rem] bg-surface-50 px-4 py-4 sm:px-5 workbench-stage-panel">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt,.md"
        multiple
        hidden
        onChange={onInlineUpload}
      />

      {selectedReferenceFiles.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {selectedReferenceFiles.map((file) => (
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
          ))}
        </div>
      ) : null}

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

      <div className="flex flex-col gap-3 pt-2 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onOpenFilePicker}
            aria-label="Upload reference files"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-text-secondary hover:text-text-main hover:bg-surface-100 transition-all font-medium text-sm"
          >
            <FileAddOutlined />
            Upload references
          </button>
        </div>

        <button
          type="button"
          onClick={onSend}
          disabled={!input.trim() || isStreaming}
          aria-label="Send prompt"
          className="inline-flex h-11 items-center justify-center gap-2 px-6 rounded-xl bg-primary-500 text-white font-medium hover:bg-primary-600 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          {isStreaming ? <LoadingOutlined /> : null}
          Generate Outline
        </button>
      </div>

      <div className="border-t border-border/30 pt-3.5 mt-2">
        <ConfigurationPanel />
      </div>
    </div>
  </div>
));
