import { memo } from 'react';
import { CopyOutlined, EditOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';
import { Input, Tooltip } from 'antd';
import type { ChatMessagePublic } from '../../api/types/chatMessage.types';
import { cn } from '../../utils/classnames';
import { ActionBubble } from '../generation/ActionBubble';
import { OutlineEditor } from '../generation/OutlineEditor';
import { isPresentationOutlineMarkdown } from './chatLogic';

const { TextArea } = Input;

interface ChatMessageItemProps {
  message: ChatMessagePublic;
  isStreaming: boolean;
  hasMessages: boolean;
  editingMessageId: string | null;
  editingContent: string;
  onEditingContentChange: (value: string) => void;
  onCopyMessage: (content: string) => void;
  onEditMessageStart: (messageId: string, content: string) => void;
  onEditMessageCancel: () => void;
  onEditMessageSubmit: () => void;
  onOutlineChange: (messageId: string, content: string) => void;
  onRefreshOutline: () => void;
  formatTime: (dateString: string) => string;
}

export const ChatMessageItem = memo(({
  message,
  isStreaming,
  hasMessages,
  editingMessageId,
  editingContent,
  onEditingContentChange,
  onCopyMessage,
  onEditMessageStart,
  onEditMessageCancel,
  onEditMessageSubmit,
  onOutlineChange,
  onRefreshOutline,
  formatTime,
}: ChatMessageItemProps) => {
  const isOutlineMessage =
    message.role === 'assistant' && isPresentationOutlineMarkdown(message.content);

  return (
    <div
      className={cn(
        'flex flex-col gap-4',
        message.role === 'user' ? 'items-end' : 'items-start'
      )}
    >
      <div
        className={cn(
          'flex gap-4',
          isOutlineMessage ? 'w-full max-w-[min(100%,78rem)]' : 'max-w-4xl',
          message.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
        )}
      >
        <div
          className={cn(
            'mt-1 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl border',
            message.role === 'assistant'
              ? 'border-brand-border bg-brand-surface text-brand-strong'
              : 'border-border/70 bg-surface-100 text-text-secondary'
          )}
        >
          {message.role === 'assistant' ? <RobotOutlined /> : <UserOutlined />}
        </div>

        <div
          className={cn(
            'min-w-0',
            isOutlineMessage
              ? 'w-full max-w-[min(100%,72rem)] flex-1'
              : 'max-w-[min(100%,42rem)]'
          )}
        >
          <div className="mb-2 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-[0.14em] text-text-secondary">
            <span>{message.role === 'assistant' ? 'Presentation Assistant' : 'Your Prompt'}</span>
            <span>·</span>
            <span>{formatTime(message.create_time)}</span>
          </div>

          {editingMessageId === message.id ? (
            <div className="flex flex-col rounded-[1.75rem] bg-surface-50 transition-all duration-300 min-w-[280px] sm:min-w-[360px]">
              <TextArea
                autoSize={{ minRows: 1, maxRows: 8 }}
                value={editingContent}
                onChange={(event) => onEditingContentChange(event.target.value)}
                className="!rounded-[1.75rem] !border-0 !bg-transparent focus:!bg-transparent focus:!ring-0 transition-all !text-text-main px-5 pt-4 pb-2 leading-7 text-sm resize-none"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    onEditMessageSubmit();
                  }
                }}
              />
              <div className="flex justify-end gap-2 px-4 pb-3 pt-1">
                <button
                  type="button"
                  onClick={onEditMessageCancel}
                  className="px-4 py-1.5 rounded-xl bg-surface-100 text-text-main text-xs font-medium shadow-sm border border-border/70 hover:bg-surface-200 hover:border-border active:scale-[0.98] transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={onEditMessageSubmit}
                  className="px-4 py-1.5 rounded-xl bg-primary-500 text-white text-xs font-medium hover:bg-primary-600 active:scale-[0.98] transition-all cursor-pointer"
                >
                  Send
                </button>
              </div>
            </div>
          ) : isOutlineMessage ? (
            <OutlineEditor
              value={message.content}
              onChange={(nextContent) => onOutlineChange(message.id, nextContent)}
              onRefresh={onRefreshOutline}
              refreshDisabled={isStreaming || !hasMessages}
              refreshing={isStreaming}
            />
          ) : (
            <div className={cn('flex flex-col', message.role === 'user' ? 'items-end group/user' : '')}>
              <div
                className={cn(
                  'rounded-[1.75rem] border px-5 py-4 text-sm leading-7 shadow-sm',
                  message.role === 'assistant'
                    ? 'border-border/70 bg-surface-50 text-text-main'
                    : 'border-brand-border bg-brand-surface/60 text-text-main'
                )}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
              {message.role === 'user' ? (
                <div className="mt-2 flex items-center justify-end gap-1.5 pr-1 text-text-secondary opacity-0 pointer-events-none transition-opacity duration-150 group-hover/user:opacity-100 group-hover/user:pointer-events-auto">
                  <Tooltip title="Copy">
                    <button
                      type="button"
                      onClick={() => onCopyMessage(message.content)}
                      aria-label="Copy message"
                      className="flex h-9 w-9 items-center justify-center rounded-md border-0 bg-transparent text-text-secondary transition-colors hover:bg-surface-100/80 hover:text-text-main"
                    >
                      <CopyOutlined className="text-[0.9rem]" />
                    </button>
                  </Tooltip>
                  <Tooltip title="Edit">
                    <button
                      type="button"
                      onClick={() => onEditMessageStart(message.id, message.content)}
                      disabled={isStreaming}
                      aria-label="Edit message"
                      className="flex h-9 w-9 items-center justify-center rounded-md border-0 bg-transparent text-text-secondary transition-colors hover:bg-surface-100/80 hover:text-text-main disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <EditOutlined className="text-[0.9rem]" />
                    </button>
                  </Tooltip>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {isOutlineMessage ? (
        <div className="mr-auto flex w-full max-w-[min(100%,78rem)] gap-4">
          <div className="mt-1 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl border border-brand-border bg-brand-surface text-brand-strong">
            <RobotOutlined />
          </div>
          <div className="min-w-0 w-full max-w-[min(100%,72rem)] flex-1">
            <div className="mb-2 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-[0.14em] text-text-secondary">
              <span>Presentation Assistant</span>
              <span>·</span>
              <span>Ready to export</span>
            </div>
            <ActionBubble markdownContent={message.content} />
          </div>
        </div>
      ) : null}
    </div>
  );
});
