import { useState, useEffect, useRef } from 'react';
import {
  SendOutlined,
  PaperClipOutlined,
  UserOutlined,
  RobotOutlined,
  ReloadOutlined,
  LoadingOutlined,
  MenuUnfoldOutlined,
  CopyOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { Button, Input, Tooltip, Spin, message } from 'antd';
import type { InputRef } from 'antd';
import { cn } from '../../utils/classnames';
import { useChatStore } from '../../store/chatStore';
import { useGenerationStore } from '../../store/generationStore';
import { useAuthStore } from '../../store/authStore';
import { useSSE } from '../../hooks/useSSE';
import { slidegenApi } from '../../api/endpoints/slidegen';
import { sessionsApi } from '../../api/endpoints/sessions';
import { chatMessagesApi } from '../../api/endpoints/chatMessages';
import { useFiles } from '../../hooks/useFiles';
import { useSession, useUpdateSession } from '../../hooks/useSessions';
import { useLayoutContext } from '../../context/LayoutContext';
import type { SSEEvent } from '../../api/types/slidegen.types';
import { getAssistantMessageContent, shouldCreateSessionForSend } from './chatLogic';
import { getCurrentFileIds } from './chatFiles';
import {
  getChatHeaderTitle,
  getUpdatedSessionTitle,
  shouldSubmitTitleChange,
} from './chatSessionTitle';
import { OutlineEditor } from '../generation/OutlineEditor';


const { TextArea } = Input;

export const ChatInterface = () => {
  const [input, setInput] = useState('');
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const loadedSessionIdRef = useRef<string | null>(null);
  const titleInputRef = useRef<InputRef>(null);
  const skipTitleBlurSubmitRef = useRef(false);
  
  // Store hooks
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
  
  const { getGenerationRequest, setStep, setMarkdownContent } = useGenerationStore();
  const { user } = useAuthStore();
  const { data: filesData } = useFiles(currentSessionId ? { session_id: currentSessionId } : undefined);
  const { data: currentSession } = useSession(currentSessionId || '');
  const updateSessionMutation = useUpdateSession();
  
  // Layout context for right panel toggle
  const { rightPanelCollapsed, setRightPanelCollapsed } = useLayoutContext();
  const currentFileIds = getCurrentFileIds(filesData);
  const currentSessionTitle = currentSession?.title || '';
  const chatHeaderTitle = getChatHeaderTitle(currentSessionTitle);

  // SSE hook for streaming responses
  const { connect: connectSSE, disconnect: disconnectSSE, isConnected } = useSSE({
    onMessage: (event: SSEEvent) => {
      // Handle content generation events
      if (event.event === 'content_generated' && 'content' in event) {
        appendStreamChunk(event.content);
      }
      if (event.event === 'step_completed' && 'content' in event && event.content) {
        appendStreamChunk(event.content);
      }
      if (event.event === 'loop_iteration_completed' && 'content' in event && event.content) {
        appendStreamChunk('\n\n' + event.content);
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
      
      // Persist assistant message to backend
      if (currentSessionId && assistantContent) {
        try {
          await chatMessagesApi.addMessage(currentSessionId, {
            session_id: currentSessionId,
            role: 'assistant',
            content: assistantContent,
          });
        } catch (err) {
          console.error('Failed to save assistant message:', err);
        }
      }
    },
    onError: (err) => {
      setStreaming(false);
      message.error(err.message || 'Generation failed');
    },
  });

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  useEffect(() => {
    if (currentSessionId && loadedSessionIdRef.current !== currentSessionId) {
        loadedSessionIdRef.current = currentSessionId;
        loadMessages(currentSessionId);
    }
  }, [currentSessionId, loadMessages]);

  useEffect(() => {
    if (!isEditingTitle) {
      setTitleDraft(chatHeaderTitle);
    }
  }, [chatHeaderTitle, isEditingTitle]);

  useEffect(() => {
    if (isEditingTitle) {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }
  }, [isEditingTitle]);

  // Clear error after 5 seconds
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
          title: 'New Presentation',
          status: 'active',
        });
        sessionId = newSession.id;
        setCurrentSession(sessionId);
      } catch {
        message.error('Failed to create session');
        return;
      }
    }
    
    // Send user message
    const savedMessage = await sendMessage(userContent);
    if (!savedMessage) return;

    // Start AI response generation
    if (user && sessionId) {
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
    resetChat();
    
    // Create a new session
    if (user) {
      try {
        const newSession = await sessionsApi.create({
          title: 'New Presentation',
          status: 'active',
        });
        setCurrentSession(newSession.id);
      } catch {
        message.error('Failed to create new session');
      }
    }
  };

  const handleGenerate = () => {
    if (currentSessionId && user) {
      setStep('generating');
      const lastUserMessage = messages.filter(m => m.role === 'user').pop();
      if (lastUserMessage) {
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
    if (!currentSessionId || updateSessionMutation.isPending) {
      return;
    }

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

  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      message.success('Copied!');
    } catch {
      message.error('Failed to copy');
    }
  };

  const handleEditMessageStart = (msgId: string, content: string) => {
    setEditingMessageId(msgId);
    setEditingContent(content);
  };

  const handleEditMessageSubmit = async () => {
    if (!editingContent.trim() || !editingMessageId) return;
    setInput(editingContent.trim());
    setEditingMessageId(null);
    setEditingContent('');
  };

  const isOutlineMarkdown = (content: string) =>
    /^#\s+/m.test(content) && /^##\s+/m.test(content);

  return (
    <div className="flex flex-col h-full bg-transparent relative">
      {/* Top Header Strip */}
      <div className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-surface-50/20 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-2 h-2 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.6)]",
            isConnected || isStreaming ? "bg-accent-cyan animate-pulse shadow-[0_0_15px_rgba(6,182,212,0.6)]" : "bg-green-500"
          )}></div>
          {isEditingTitle ? (
            <Input
              ref={titleInputRef}
              value={titleDraft}
              onChange={(event) => setTitleDraft(event.target.value)}
              onBlur={() => void handleTitleInputBlur()}
              onKeyDown={(event) => {
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
              className="w-[min(28rem,55vw)]"
            />
          ) : (
            <button
              type="button"
              onClick={handleTitleEditStart}
              disabled={!currentSessionId || updateSessionMutation.isPending}
              className={cn(
                'm-0 max-w-[min(28rem,55vw)] truncate border-0 bg-transparent p-0 text-left text-lg font-bold tracking-tight text-text-main transition-colors',
                currentSessionId
                  ? 'cursor-text hover:text-primary-300'
                  : 'cursor-default'
              )}
              title={currentSessionId ? 'Click to rename this session' : chatHeaderTitle}
            >
              {chatHeaderTitle}
            </button>
          )}
          {isStreaming && <Spin size="small" indicator={<LoadingOutlined spin className="text-primary-400" />} />}
        </div>
        <div className="flex items-center gap-2">
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleReset}
            disabled={isStreaming}
            className="!bg-white/5 !border-white/10 !text-text-secondary hover:!text-text-main hover:!bg-white/10 hover:!border-white/20 transition-all"
          >
            Reset Chat
          </Button>
          {rightPanelCollapsed && (
            <Tooltip title="Open Configuration Panel">
              <Button 
                icon={<MenuUnfoldOutlined />} 
                onClick={() => setRightPanelCollapsed(false)}
                className="!bg-white/5 !border-white/10 !text-text-secondary hover:!text-text-main hover:!bg-white/10 hover:!border-white/20 transition-all"
              />
            </Tooltip>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mx-8 mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm backdrop-blur-sm">
          {error}
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-6 custom-scrollbar">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <Spin size="large" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-text-secondary">
            <div className="w-20 h-20 rounded-2xl bg-primary-gradient/10 flex items-center justify-center mb-6 shadow-glow-strong">
              <RobotOutlined className="text-4xl text-primary-400" />
            </div>
            <p className="text-xl font-semibold text-text-main mb-2">Start a conversation to create your presentation</p>
            <p className="text-sm opacity-60 max-w-md text-center">Describe your presentation topic, target audience, and any specific requirements you have in mind.</p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-4 animate-slide-up",
                  msg.role === 'assistant' && isOutlineMarkdown(msg.content)
                    ? "w-full max-w-[min(100%,78rem)]"
                    : "max-w-3xl",
                  msg.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                {/* Avatar */}
                <div className={cn(
                  "w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-1 shadow-lg",
                  msg.role === 'assistant'
                    ? "bg-primary-gradient shadow-glow"
                    : "bg-surface-500/30 border border-white/5"
                )}>
                  {msg.role === 'assistant' ? <RobotOutlined className="text-white text-lg" /> : <UserOutlined className="text-text-secondary" />}
                </div>

                {/* Bubble */}
                <div className={cn(
                  "flex flex-col gap-1 min-w-0",
                  msg.role === 'assistant' && isOutlineMarkdown(msg.content)
                    ? "w-full max-w-[min(100%,72rem)] flex-1"
                    : "max-w-[85%]",
                  msg.role === 'user' ? "items-end" : "items-start"
                )}>
                  {editingMessageId === msg.id ? (
                    <div className="w-full flex flex-col gap-2">
                      <TextArea
                        autoSize={{ minRows: 2, maxRows: 8 }}
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        className="!bg-surface-100/40 !border-primary-500/50 !text-text-main !rounded-2xl"
                        autoFocus
                      />
                      <div className="flex gap-2 justify-end">
                        <Button size="small" onClick={() => setEditingMessageId(null)}>Cancel</Button>
                        <Button size="small" type="primary" onClick={() => void handleEditMessageSubmit()}>
                          Edit &amp; Resend
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div
                      className={cn(
                        "group/bubble relative",
                        msg.role === 'assistant' && isOutlineMarkdown(msg.content) && "w-full"
                      )}
                    >
                      {msg.role === 'assistant' && isOutlineMarkdown(msg.content) ? (
                        <div className="w-full rounded-[30px] rounded-tl-none">
                          <OutlineEditor
                            value={msg.content}
                            onChange={(nextContent) => {
                              updateLocalMessage(msg.id, nextContent);
                              setMarkdownContent(nextContent);
                            }}
                          />
                        </div>
                      ) : (
                        <div className={cn(
                          "px-6 py-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap shadow-sm",
                          msg.role === 'assistant'
                            ? "bg-surface-100/40 backdrop-blur-md text-text-main rounded-tl-none border border-white/5"
                            : "bg-primary-gradient text-white rounded-tr-none shadow-glow font-medium"
                        )}>
                          {msg.content}
                        </div>
                      )}
                      {msg.role === 'user' && (
                        <div className="flex gap-1 justify-end mt-1 opacity-0 group-hover/bubble:opacity-100 transition-opacity duration-150">
                          <Tooltip title="Copy">
                            <button
                              type="button"
                              onClick={() => void handleCopyMessage(msg.content)}
                              className="w-7 h-7 flex items-center justify-center rounded-lg bg-surface-200/40 hover:bg-surface-200/70 text-text-secondary hover:text-text-main transition-colors"
                            >
                              <CopyOutlined className="text-xs" />
                            </button>
                          </Tooltip>
                          <Tooltip title="Edit">
                            <button
                              type="button"
                              onClick={() => handleEditMessageStart(msg.id, msg.content)}
                              disabled={isStreaming}
                              className="w-7 h-7 flex items-center justify-center rounded-lg bg-surface-200/40 hover:bg-surface-200/70 text-text-secondary hover:text-text-main transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            >
                              <EditOutlined className="text-xs" />
                            </button>
                          </Tooltip>
                        </div>
                      )}
                    </div>
                  )}
                  <span className="text-[10px] text-text-secondary/60 px-1 font-medium tracking-wide">
                    {msg.role === 'assistant' ? 'AI ASSISTANT' : 'YOU'} • {formatTime(msg.create_time)}
                  </span>
                </div>
              </div>
            ))}

            {/* Streaming message */}
            {isStreaming && streamingContent && (
              <div className="flex gap-4 max-w-3xl mr-auto animate-slide-up">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-1 bg-primary-gradient shadow-glow">
                  <RobotOutlined className="text-white text-lg" />
                </div>
                <div className="flex flex-col gap-1 min-w-0 max-w-[85%] items-start">
                  <div className="px-6 py-4 rounded-2xl text-sm leading-relaxed bg-surface-100/40 backdrop-blur-md text-text-main rounded-tl-none border border-white/5 whitespace-pre-wrap shadow-sm">
                    {streamingContent}
                    <span className="inline-block w-1.5 h-4 bg-primary-400 ml-1 animate-pulse align-middle rounded-full"></span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 sm:p-8 pt-0 bg-transparent">
        <div className="max-w-4xl mx-auto relative group">
          <div className="relative bg-surface-50/60 backdrop-blur-xl rounded-2xl border border-white/10 transition-all duration-300 p-2 flex flex-col gap-2 shadow-glass group-focus-within:border-primary-500/50 group-focus-within:shadow-glow/20 group-focus-within:bg-surface-50/80">
            <TextArea 
              placeholder="Describe your presentation topic..."
              autoSize={{ minRows: 1, maxRows: 6 }}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={isStreaming}
              className="!bg-transparent !border-none !text-text-main !shadow-none !px-3 !py-2 !text-base placeholder:!text-text-muted/70"
            />
            
            <div className="flex items-center justify-between px-2 pb-1">
              <div className="flex gap-2">
                <Tooltip title="Upload Reference">
                  <Button 
                    type="text" 
                    size="small"
                    icon={<PaperClipOutlined />} 
                    className="!text-text-secondary hover:!text-primary-400 hover:!bg-primary-500/10 transition-colors"
                  />
                </Tooltip>
              </div>
              
              <Button
                type="primary"
                icon={isStreaming ? <LoadingOutlined /> : <SendOutlined />}
                onClick={handleSend}
                disabled={!input.trim() || isStreaming}
                className={cn(
                  "!flex items-center justify-center !w-9 !h-9 !min-w-0 !rounded-xl transition-all duration-300",
                   !input.trim() || isStreaming ? "!bg-surface-300 !text-text-secondary" : "!bg-primary-gradient !shadow-glow hover:!opacity-90 hover:!scale-105"
                )}
              />
            </div>
          </div>
          
          {/* Footer Status */}
          <div className="flex justify-between items-center mt-3 px-2">
            <div className="flex items-center gap-2">
              <span className={cn(
                "w-1.5 h-1.5 rounded-full shadow-lg",
                isStreaming ? "bg-accent-cyan animate-pulse shadow-accent-cyan/50" : "bg-green-500 shadow-green-500/50"
              )}></span>
              <span className="text-[10px] text-text-secondary font-medium tracking-wide uppercase">
                {isStreaming ? 'Generating...' : 'System Ready'}
              </span>
            </div>
            <Button
              type="link"
              onClick={handleGenerate}
              disabled={isStreaming || messages.length === 0}
              className={cn(
                "!text-[11px] !p-0 !h-auto font-bold tracking-wider transition-colors",
                isStreaming || messages.length === 0 ? "!text-text-secondary/30" : "!text-primary-400 hover:!text-primary-300"
              )}
            >
              ✨ GENERATE SLIDES
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
