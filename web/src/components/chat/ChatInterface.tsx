import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { RobotOutlined } from '@ant-design/icons';
import { Input, Spin, message } from 'antd';
import type { InputRef } from 'antd';
import { cn } from '../../utils/classnames';
import { useChatStore } from '../../store/chatStore';
import { useGenerationStore } from '../../store/generationStore';
import { useAuthStore } from '../../store/authStore';
import { slidegenApi } from '../../api/endpoints/slidegen';
import { useDeleteFile, useFiles, useUploadFile } from '../../hooks/useFiles';
import { useCreateSession, useSession, useUpdateSession } from '../../hooks/useSessions';
import { SessionStatus } from '../../api/types/session.types';
import { shouldCreateSessionForSend } from './chatLogic';
import { getCurrentFileIds } from './chatFiles';
import {
  getChatHeaderTitle,
  getUpdatedSessionTitle,
  shouldSubmitTitleChange,
} from './chatSessionTitle';
import { ComposerCard } from './ComposerCard';
import { ChatMessageItem } from './ChatMessageItem';
import { usePresentationStream } from './usePresentationStream';
import { DEFAULT_PRESENTATION_TITLE } from '../../utils/constants';

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
    clearError,
  } = useChatStore();

  const { getGenerationRequest, setStep, setMarkdownContent } = useGenerationStore();
  const { user } = useAuthStore();
  const { data: filesData } = useFiles(currentSessionId ? { session_id: currentSessionId } : undefined);
  const { data: currentSession } = useSession(currentSessionId || '');
  const createSessionMutation = useCreateSession();
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
  const primaryUserMessage = messages.find((messageItem) => messageItem.role === 'user')?.content;
  const chatHeaderTitle = getChatHeaderTitle(
    resolvedSessionTitle,
    currentSession?.topic,
    primaryUserMessage
  );
  const hasMessages = messages.length > 0;
  const { startPresentationStream } = usePresentationStream({
    currentSessionId,
    streamingContent,
    appendStreamChunk,
    finalizeStreamingMessage,
    setStreaming,
    setMarkdownContent,
    setStep,
    onStreamError: () => {
      shouldAutoScrollToGenerationRef.current = false;
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

  const beginPresentationStream = (prompt: string, sessionId: string) => {
    if (!user) return;

    shouldAutoScrollToGenerationRef.current = true;
    setStreaming(true);
    const request = getGenerationRequest(prompt, user.id, sessionId, currentFileIds);
    const streamRequest = slidegenApi.getMarkdownStreamRequest(request);
    startPresentationStream(streamRequest);
  };

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
        const newSession = await createSessionMutation.mutateAsync({
          title: DEFAULT_PRESENTATION_TITLE,
          status: SessionStatus.ACTIVE,
        });
        sessionId = newSession.id;
        setCurrentSession(sessionId);
      } catch {
        return;
      }
    }

    const savedMessage = await sendMessage(userContent);
    if (!savedMessage || !user || !sessionId) return;

    beginPresentationStream(userContent, sessionId);
  };

  const handleGenerate = () => {
    if (!currentSessionId || !user) return;

    setStep('generating');
    const lastUserMessage = messages.filter((messageItem) => messageItem.role === 'user').pop();
    if (lastUserMessage) {
      beginPresentationStream(lastUserMessage.content, currentSessionId);
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

  const handleEditMessageSubmit = () => {
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

  const handleOutlineChange = (messageId: string, nextContent: string) => {
    updateLocalMessage(messageId, nextContent);
    setMarkdownContent(nextContent);
  };

  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const renderComposerCard = () => (
    <ComposerCard
      input={input}
      isStreaming={isStreaming}
      hasMessages={hasMessages}
      selectedReferenceFiles={selectedReferenceFiles}
      fileInputRef={fileInputRef}
      onInputChange={setInput}
      onSend={() => void handleSend()}
      onGenerate={handleGenerate}
      onOpenFilePicker={handleOpenFilePicker}
      onInlineUpload={(event) => void handleInlineUpload(event)}
      onRemoveReferenceFile={(fileId) => void handleRemoveReferenceFile(fileId)}
    />
  );

  return (
    <div className="workbench-page relative flex h-full flex-col bg-transparent">
      <div className="border-b border-border/70 bg-surface-50/88 px-4 py-3 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-5xl items-center">
          <div className="min-w-0 flex-1">
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
                className="!h-8 w-full max-w-full !text-[15px] sm:w-[min(32rem,60vw)]"
              />
            ) : (
              <button
                type="button"
                onClick={handleTitleEditStart}
                disabled={!currentSessionId || updateSessionMutation.isPending}
                className={cn(
                  'm-0 max-w-full truncate border-0 bg-transparent p-0 text-left text-[15px] font-semibold tracking-tight text-text-main transition-colors sm:max-w-[min(34rem,62vw)] sm:text-[16px]',
                  currentSessionId ? 'cursor-text hover:text-brand-strong' : 'cursor-default'
                )}
                title={currentSessionId ? 'Click to rename this project' : chatHeaderTitle}
              >
                {chatHeaderTitle}
              </button>
            )}
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
                {messages.map((messageItem) => (
                  <ChatMessageItem
                    key={messageItem.id}
                    message={messageItem}
                    isStreaming={isStreaming}
                    hasMessages={hasMessages}
                    editingMessageId={editingMessageId}
                    editingContent={editingContent}
                    onEditingContentChange={setEditingContent}
                    onCopyMessage={(content) => void handleCopyMessage(content)}
                    onEditMessageStart={handleEditMessageStart}
                    onEditMessageCancel={() => setEditingMessageId(null)}
                    onEditMessageSubmit={handleEditMessageSubmit}
                    onOutlineChange={handleOutlineChange}
                    onRefreshOutline={handleGenerate}
                    formatTime={formatTime}
                  />
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
            <div className="mx-auto flex h-full max-w-5xl flex-col justify-center">
              {renderComposerCard()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
