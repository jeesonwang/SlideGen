import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import {
  BgColorsOutlined,
  CopyOutlined,
  DownOutlined,
  EditOutlined,
  FileAddOutlined,
  FileTextOutlined,
  LoadingOutlined,
  ReloadOutlined,
  RobotOutlined,
  SendOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Button, Dropdown, Input, Spin, Tooltip, message } from 'antd';
import type { InputRef } from 'antd';
import type { MenuProps } from 'antd';
import { cn } from '../../utils/classnames';
import { useChatStore } from '../../store/chatStore';
import { useGenerationStore } from '../../store/generationStore';
import { useAuthStore } from '../../store/authStore';
import { useSSE } from '../../hooks/useSSE';
import { slidegenApi } from '../../api/endpoints/slidegen';
import { sessionsApi } from '../../api/endpoints/sessions';
import { chatMessagesApi } from '../../api/endpoints/chatMessages';
import { useDeleteFile, useFiles, useUploadFile } from '../../hooks/useFiles';
import { useSession, useUpdateSession } from '../../hooks/useSessions';
import { useTemplates } from '../../hooks/useTemplates';
import type { SSEEvent } from '../../api/types/slidegen.types';
import { getAssistantMessageContent, shouldCreateSessionForSend } from './chatLogic';
import { getCurrentFileIds } from './chatFiles';
import {
  getChatHeaderTitle,
  getUpdatedSessionTitle,
  shouldSubmitTitleChange,
} from './chatSessionTitle';
import { OutlineEditor } from '../generation/OutlineEditor';
import { ConfigurationPanel } from '../config/ConfigurationPanel';
import { DEFAULT_PRESENTATION_TITLE } from '../../utils/constants';

const { TextArea } = Input;

export const ChatInterface = () => {
  const [input, setInput] = useState('');
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState('');
  const [optimisticTitleState, setOptimisticTitleState] = useState<{
    sessionId: string;
    title: string;
  } | null>(null);
  const activeGenerationRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollToGenerationRef = useRef(false);
  const loadedSessionIdRef = useRef<string | null>(null);
  const titleInputRef = useRef<InputRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const skipTitleBlurSubmitRef = useRef(false);

  const {
    currentSessionId,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    setCurrentSession,
    loadMessages,
    sendMessage,
    updateLocalMessage,
    appendStreamChunk,
    finalizeStreamingMessage,
    setStreaming,
    resetChat,
    clearError,
  } = useChatStore();

  const { getGenerationRequest, setStep, setMarkdownContent, template, setTemplate } =
    useGenerationStore();
  const { user } = useAuthStore();
  const { data: filesData } = useFiles(currentSessionId ? { session_id: currentSessionId } : undefined);
  const { data: currentSession } = useSession(currentSessionId || '');
  const { data: templates } = useTemplates();
  const updateSessionMutation = useUpdateSession();
  const uploadFileMutation = useUploadFile();
  const deleteFileMutation = useDeleteFile();

  const selectedReferenceFiles = filesData?.data || [];
  const currentFileIds = getCurrentFileIds(filesData);
  const currentSessionTitle = currentSession?.title || '';
  const optimisticSessionTitle =
    optimisticTitleState?.sessionId === currentSessionId ? optimisticTitleState.title : null;
  const resolvedSessionTitle =
    optimisticSessionTitle && optimisticSessionTitle.trim() !== currentSessionTitle.trim()
      ? optimisticSessionTitle
      : currentSessionTitle;
  const primaryUserMessage = messages.find((message) => message.role === 'user')?.content;
  const chatHeaderTitle = getChatHeaderTitle(
    resolvedSessionTitle,
    currentSession?.topic,
    primaryUserMessage
  );
  const currentProjectStatus = currentSessionId ? 'Project ready' : 'Start with a topic';
  const selectedTemplateLabel =
    templates?.find((item) => item.id === template)?.name || 'General';
  const templateMenuItems: MenuProps['items'] =
    templates?.map((item) => ({
      key: item.id,
      label: item.name,
    })) || [
      {
        key: 'general',
        label: 'General',
      },
    ];

  const { connect: connectSSE, disconnect: disconnectSSE, isConnected } = useSSE({
    onMessage: (event: SSEEvent) => {
      if (event.event === 'content_generated' && 'content' in event) {
        appendStreamChunk(event.content);
      }
      if (event.event === 'step_completed' && 'content' in event && event.content) {
        appendStreamChunk(event.content);
      }
      if (event.event === 'loop_iteration_completed' && 'content' in event && event.content) {
        appendStreamChunk(`\n\n${event.content}`);
      }
    },
    onComplete: async (finalContent: string) => {
      const assistantContent = getAssistantMessageContent({
        finalContent,
        streamingContent,
      });

      finalizeStreamingMessage(assistantContent);
      setMarkdownContent(assistantContent);
      setStep('editing');

      if (currentSessionId && assistantContent) {
        try {
          await chatMessagesApi.addMessage(currentSessionId, {
            session_id: currentSessionId,
            role: 'assistant',
            content: assistantContent,
          });
        } catch (saveError) {
          console.error('Failed to save assistant message:', saveError);
        }
      }
    },
    onError: (streamError) => {
      shouldAutoScrollToGenerationRef.current = false;
      setStreaming(false);
      message.error(streamError.message || 'Generation failed. Please try again.');
    },
  });

  useEffect(() => {
    if (!shouldAutoScrollToGenerationRef.current || !activeGenerationRef.current) {
      return;
    }

    activeGenerationRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    shouldAutoScrollToGenerationRef.current = false;
  }, [isStreaming, streamingContent, messages.length]);

  useEffect(() => {
    if (currentSessionId && loadedSessionIdRef.current !== currentSessionId) {
      loadedSessionIdRef.current = currentSessionId;
      loadMessages(currentSessionId);
    }
  }, [currentSessionId, loadMessages]);

  useEffect(() => {
    if (isEditingTitle) {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }
  }, [isEditingTitle]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming || isLoading) return;

    const userContent = input.trim();
    setInput('');
    let sessionId = currentSessionId;

    if (
      shouldCreateSessionForSend({
        currentSessionId: sessionId,
        hasUser: !!user,
        content: userContent,
      })
    ) {
      try {
        const newSession = await sessionsApi.create({
          title: DEFAULT_PRESENTATION_TITLE,
          status: 'active',
        });
        sessionId = newSession.id;
        setCurrentSession(sessionId);
      } catch {
        message.error('Failed to create presentation project');
        return;
      }
    }

    const savedMessage = await sendMessage(userContent);
    if (!savedMessage) return;

    if (user && sessionId) {
      shouldAutoScrollToGenerationRef.current = true;
      setStreaming(true);
      const request = getGenerationRequest(userContent, user.id, sessionId, currentFileIds);
      const streamRequest = slidegenApi.getMarkdownStreamRequest(request);
      connectSSE(streamRequest);
    }
  };

  const handleReset = async () => {
    if (isStreaming) {
      disconnectSSE();
      setStreaming(false);
    }
    shouldAutoScrollToGenerationRef.current = false;
    resetChat();

    if (user) {
      try {
        const newSession = await sessionsApi.create({
          title: DEFAULT_PRESENTATION_TITLE,
          status: 'active',
        });
        setCurrentSession(newSession.id);
      } catch {
        message.error('Failed to create presentation project');
      }
    }
  };

  const handleGenerate = () => {
    if (currentSessionId && user) {
      setStep('generating');
      const lastUserMessage = messages.filter((msg) => msg.role === 'user').pop();
      if (lastUserMessage) {
        shouldAutoScrollToGenerationRef.current = true;
        setStreaming(true);
        const request = getGenerationRequest(
          lastUserMessage.content,
          user.id,
          currentSessionId,
          currentFileIds
        );
        const streamRequest = slidegenApi.getMarkdownStreamRequest(request);
        connectSSE(streamRequest);
      }
    }
  };

  const handleTitleEditStart = () => {
    if (!currentSessionId || updateSessionMutation.isPending) return;
    setTitleDraft(chatHeaderTitle);
    setIsEditingTitle(true);
  };

  const handleTitleEditCancel = () => {
    skipTitleBlurSubmitRef.current = true;
    setTitleDraft(chatHeaderTitle);
    setIsEditingTitle(false);
  };

  const handleTitleSubmit = async () => {
    if (!currentSessionId) {
      setIsEditingTitle(false);
      return;
    }

    const nextTitle = getUpdatedSessionTitle(titleDraft, currentSessionTitle);
    if (!nextTitle) {
      setTitleDraft(chatHeaderTitle);
      setIsEditingTitle(false);
      return;
    }

    if (!shouldSubmitTitleChange(titleDraft, currentSessionTitle)) {
      setTitleDraft(nextTitle);
      setIsEditingTitle(false);
      return;
    }

    try {
      await updateSessionMutation.mutateAsync({
        id: currentSessionId,
        data: { title: nextTitle },
      });
      setOptimisticTitleState({
        sessionId: currentSessionId,
        title: nextTitle,
      });
      setTitleDraft(nextTitle);
      setIsEditingTitle(false);
    } catch {
      setTitleDraft(chatHeaderTitle);
    }
  };

  const handleTitleInputBlur = async () => {
    if (skipTitleBlurSubmitRef.current) {
      skipTitleBlurSubmitRef.current = false;
      return;
    }

    await handleTitleSubmit();
  };

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      message.success('Copied');
    } catch {
      message.error('Copy failed');
    }
  };

  const handleEditMessageStart = (messageId: string, content: string) => {
    setEditingMessageId(messageId);
    setEditingContent(content);
  };

  const handleEditMessageSubmit = async () => {
    if (!editingContent.trim() || !editingMessageId) return;
    setInput(editingContent.trim());
    setEditingMessageId(null);
    setEditingContent('');
  };

  const handleOpenFilePicker = () => {
    if (!currentSessionId) {
      message.warning('Create or open a project before uploading references.');
      return;
    }

    fileInputRef.current?.click();
  };

  const handleInlineUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (!currentSessionId) {
      message.warning('Create or open a project before uploading references.');
      return;
    }

    await Promise.all(
      files.map((file) => uploadFileMutation.mutateAsync({ file, sessionId: currentSessionId }))
    );

    event.target.value = '';
  };

  const handleRemoveReferenceFile = async (fileId: string) => {
    await deleteFileMutation.mutateAsync(fileId);
  };

  const handleTemplateSelect: MenuProps['onClick'] = ({ key }) => {
    setTemplate(String(key));
  };

  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const isOutlineMarkdown = (content: string) => /^#\s+/m.test(content) && /^##\s+/m.test(content);
  const hasMessages = messages.length > 0;

  const renderComposerCard = () => (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8 flex flex-col gap-4 rounded-[2rem] border border-border/70 bg-background px-4 py-4 shadow-soft sm:px-5">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.doc,.docx,.txt,.md"
          multiple
          hidden
          onChange={handleInlineUpload}
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
                  onClick={() => void handleRemoveReferenceFile(file.id)}
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
          onChange={(event) => setInput(event.target.value)}
          onPressEnter={(event) => {
            if (!event.shiftKey) {
              event.preventDefault();
              void handleSend();
            }
          }}
          disabled={isStreaming}
          className="!border-none !bg-transparent !px-1 !py-2 !text-base !text-text-main !shadow-none placeholder:!text-text-muted"
        />

        <div className="flex flex-col gap-3 border-t border-border/70 pt-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="text"
              icon={<FileAddOutlined />}
              onClick={handleOpenFilePicker}
              aria-label="Upload reference files"
              className="!h-11 !rounded-xl !px-4 !text-text-secondary hover:!bg-surface-100 hover:!text-text-main"
            >
              Upload references
            </Button>

            <Button
              type="link"
              onClick={handleGenerate}
              disabled={isStreaming || !hasMessages}
              className="!h-11 !px-2 !text-xs !font-semibold !text-primary-600 disabled:!text-text-muted"
            >
              Regenerate outline
            </Button>
          </div>

          <Button
            type="primary"
            icon={isStreaming ? <LoadingOutlined /> : <SendOutlined />}
            onClick={() => void handleSend()}
            disabled={!input.trim() || isStreaming}
            aria-label="Send prompt"
            className="!h-11 !rounded-xl !px-5 !font-semibold"
          >
            Generate
          </Button>
        </div>

        <div className="border-t border-border/70 pt-4">
          <ConfigurationPanel />
        </div>
      </div>
    </div>
  );

  return (
    <div className="relative flex h-full flex-col bg-transparent">
      <div className="border-b border-border/70 bg-surface-50/95 px-4 py-4 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-5xl flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-text-secondary">
              <span
                className={cn(
                  'inline-flex h-2.5 w-2.5 rounded-full',
                  isConnected || isStreaming ? 'bg-primary-500' : 'bg-emerald-500'
                )}
              />
              {isStreaming ? 'Generating outline' : currentProjectStatus}
            </div>

            {isEditingTitle ? (
              <Input
                ref={titleInputRef}
                value={titleDraft}
                onChange={(event) => setTitleDraft(event.target.value)}
                onBlur={() => void handleTitleInputBlur()}
                onKeyDown={(event) => {
                  if (event.nativeEvent.isComposing || event.keyCode === 229) {
                    return;
                  }

                  if (event.key === 'Enter') {
                    event.preventDefault();
                    void handleTitleSubmit();
                  }

                  if (event.key === 'Escape') {
                    event.preventDefault();
                    handleTitleEditCancel();
                  }
                }}
                disabled={updateSessionMutation.isPending}
                maxLength={120}
                className="w-full max-w-full sm:w-[min(32rem,60vw)]"
              />
            ) : (
              <button
                type="button"
                onClick={handleTitleEditStart}
                disabled={!currentSessionId || updateSessionMutation.isPending}
                className={cn(
                  'm-0 max-w-full truncate border-0 bg-transparent p-0 text-left text-[clamp(1rem,0.95rem+0.2vw,1.2rem)] font-semibold tracking-tight text-text-main transition-colors sm:max-w-[min(34rem,62vw)]',
                  currentSessionId ? 'cursor-text hover:text-brand-strong' : 'cursor-default'
                )}
                title={currentSessionId ? 'Click to rename this project' : chatHeaderTitle}
              >
                {chatHeaderTitle}
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
              disabled={isStreaming}
              className="!h-11 !rounded-xl !border-border/70 !bg-surface-100 !px-4 !text-text-main hover:!border-brand-border hover:!bg-surface-50"
            >
              New project
            </Button>
          </div>
        </div>
      </div>

      {error ? (
        <div className="mx-4 mt-4 rounded-2xl border border-red-300/60 bg-red-50 px-4 py-3 text-sm text-red-600 sm:mx-6 lg:mx-8">
          {error}
        </div>
      ) : null}

      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8 custom-scrollbar">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Spin size="large" />
          </div>
        ) : (
          <></>
        )}

        <div className="mx-auto max-w-6xl">
          {hasMessages ? (
            <>
              {renderComposerCard()}
              <div className="mx-auto flex max-w-6xl flex-col gap-8">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={cn(
                      'flex gap-4',
                      msg.role === 'assistant' && isOutlineMarkdown(msg.content)
                        ? 'w-full max-w-[min(100%,78rem)]'
                        : 'max-w-4xl',
                      msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                    )}
                  >
                    <div
                      className={cn(
                        'mt-1 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl border',
                        msg.role === 'assistant'
                          ? 'border-brand-border bg-brand-surface text-brand-strong'
                          : 'border-border/70 bg-surface-100 text-text-secondary'
                      )}
                    >
                      {msg.role === 'assistant' ? <RobotOutlined /> : <UserOutlined />}
                    </div>

                    <div
                      className={cn(
                        'min-w-0',
                        msg.role === 'assistant' && isOutlineMarkdown(msg.content)
                          ? 'w-full max-w-[min(100%,72rem)] flex-1'
                          : 'max-w-[min(100%,42rem)]'
                      )}
                    >
                      <div className="mb-2 flex items-center gap-2 px-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-text-secondary">
                        <span>{msg.role === 'assistant' ? 'Presentation Assistant' : 'Your Prompt'}</span>
                        <span>·</span>
                        <span>{formatTime(msg.create_time)}</span>
                      </div>

                      {editingMessageId === msg.id ? (
                        <div className="space-y-3 rounded-[1.5rem] border border-brand-border bg-surface-50 p-4">
                          <TextArea
                            autoSize={{ minRows: 2, maxRows: 8 }}
                            value={editingContent}
                            onChange={(event) => setEditingContent(event.target.value)}
                            className="!rounded-2xl !border-border/70 !bg-surface-100 !text-text-main"
                            autoFocus
                          />
                          <div className="flex justify-end gap-2">
                            <Button size="small" onClick={() => setEditingMessageId(null)}>
                              Cancel
                            </Button>
                            <Button size="small" type="primary" onClick={() => void handleEditMessageSubmit()}>
                              Refill and regenerate
                            </Button>
                          </div>
                        </div>
                      ) : msg.role === 'assistant' && isOutlineMarkdown(msg.content) ? (
                        <OutlineEditor
                          value={msg.content}
                          onChange={(nextContent) => {
                            updateLocalMessage(msg.id, nextContent);
                            setMarkdownContent(nextContent);
                          }}
                          onRefresh={() => void handleGenerate()}
                          refreshDisabled={isStreaming || !hasMessages}
                          refreshing={isStreaming}
                          toolbarActions={
                            <Dropdown
                              trigger={['click']}
                              menu={{
                                items: templateMenuItems,
                                selectable: true,
                                selectedKeys: [template],
                                onClick: handleTemplateSelect,
                              }}
                            >
                              <button
                                type="button"
                                aria-label="Select theme"
                                className="inline-flex h-11 items-center gap-2 rounded-full border border-brand-border bg-brand-surface px-4 text-sm font-medium text-brand-strong transition-colors hover:border-brand-strong hover:text-text-main"
                              >
                                <BgColorsOutlined />
                                <span>Select theme</span>
                                <span className="max-w-28 truncate text-text-secondary">
                                  {selectedTemplateLabel}
                                </span>
                                <DownOutlined className="text-xs" />
                              </button>
                            </Dropdown>
                          }
                        />
                      ) : (
                        <div
                          className={cn(
                            'rounded-[1.75rem] border px-5 py-4 text-sm leading-7 shadow-sm',
                            msg.role === 'assistant'
                              ? 'border-border/70 bg-surface-50 text-text-main'
                              : 'border-brand-border bg-brand-surface/60 text-text-main'
                          )}
                        >
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                          {msg.role === 'user' ? (
                            <div className="mt-4 flex justify-end gap-2">
                              <Tooltip title="Copy">
                                <button
                                  type="button"
                                  onClick={() => void handleCopyMessage(msg.content)}
                                  aria-label="Copy message"
                                  className="flex h-11 w-11 items-center justify-center rounded-xl border border-border/70 bg-surface-100 text-text-secondary transition-colors hover:border-brand-border hover:text-text-main"
                                >
                                  <CopyOutlined className="text-xs" />
                                </button>
                              </Tooltip>
                              <Tooltip title="Edit">
                                <button
                                  type="button"
                                  onClick={() => handleEditMessageStart(msg.id, msg.content)}
                                  disabled={isStreaming}
                                  aria-label="Edit message"
                                  className="flex h-11 w-11 items-center justify-center rounded-xl border border-border/70 bg-surface-100 text-text-secondary transition-colors hover:border-brand-border hover:text-text-main disabled:cursor-not-allowed disabled:opacity-40"
                                >
                                  <EditOutlined className="text-xs" />
                                </button>
                              </Tooltip>
                            </div>
                          ) : null}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {isStreaming ? (
                  <div ref={activeGenerationRef} className="mr-auto flex max-w-4xl gap-4">
                    <div className="mt-1 flex h-11 w-11 items-center justify-center rounded-2xl border border-brand-border bg-brand-surface text-brand-strong">
                      <RobotOutlined />
                    </div>
                    <div className="min-w-0 max-w-[min(100%,42rem)]">
                      <div className="mb-2 flex items-center gap-2 px-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-text-secondary">
                        Presentation Assistant · Generating
                      </div>
                      <div className="rounded-[1.75rem] border border-border/70 bg-surface-50 px-5 py-4 text-sm leading-7 text-text-main shadow-sm">
                        {streamingContent || 'Preparing outline...'}
                        <span className="ml-1 inline-block h-4 w-1.5 animate-pulse rounded-full bg-primary-500 align-middle" />
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </>
          ) : (
            <div className="mx-auto flex h-full max-w-4xl flex-col justify-center">
              <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
                <section className="rounded-[2rem] border border-border/70 bg-surface-50 px-6 py-8 shadow-soft">
                  <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-surface text-brand-strong">
                    <RobotOutlined className="text-2xl" />
                  </div>
                  <h2 className="m-0 text-[clamp(1.6rem,1.35rem+0.8vw,2.25rem)] font-semibold tracking-tight text-text-main">
                    Start with a clear topic and build a presentation structure fast
                  </h2>
                  <p className="mt-4 max-w-2xl text-base leading-7 text-text-secondary">
                    Describe the topic, target audience, and the outcome you want. If you already have PDFs, Word files, or notes, upload them first and let the system organize the outline.
                  </p>
                </section>

                <section className="rounded-[2rem] border border-border/70 bg-surface-100/80 px-6 py-8">
                  <div className="text-sm font-semibold text-text-main">Prompt ingredients</div>
                  <ul className="mt-4 space-y-3 text-sm leading-6 text-text-secondary">
                    <li>State the topic and what kind of presentation you need.</li>
                    <li>Describe the audience and what they care about most.</li>
                    <li>Call out the arguments, examples, or data you want emphasized.</li>
                  </ul>
                </section>
              </div>
              {renderComposerCard()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
