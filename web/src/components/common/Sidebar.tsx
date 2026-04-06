import { useEffect, useRef, useState } from 'react';
import {
  MessageOutlined,
  AppstoreOutlined,
  FileOutlined,
  SettingOutlined,
  LogoutOutlined,
  PlusOutlined,
  LoadingOutlined,
  DeleteOutlined,
  EditOutlined,
  MoreOutlined,
  PushpinOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { Spin, Dropdown, Input, Modal, Popover, Button, Tooltip } from 'antd';
import type { InputRef, MenuProps } from 'antd';
import { cn } from '../../utils/classnames';
import {
  useSessions,
  useCreateSession,
  useDeleteSession,
  useUpdateSession,
} from '../../hooks/useSessions';
import { useAuth } from '../../hooks/useAuth';
import { useChatStore } from '../../store/chatStore';
import { useAuthStore } from '../../store/authStore';
import { useGenerationStore } from '../../store/generationStore';
import { getSessionDisplayTitle, getUpdatedSessionTitle } from '../chat/chatSessionTitle';
import {
  isSidebarSessionPinned,
  sortSidebarSessions,
  togglePinnedExtraData,
} from './sidebarSessionList';
import { getSidebarUserPanelData } from './sidebarUserPanel';
import { useUIStore } from '../../store/uiStore';
import { DEFAULT_PRESENTATION_TITLE } from '../../utils/constants';

interface SidebarProps {
  onNavigate?: () => void;
}

export const Sidebar = ({ onNavigate }: SidebarProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [titleDraft, setTitleDraft] = useState('');
  const [userPanelOpen, setUserPanelOpen] = useState(false);
  const titleInputRef = useRef<InputRef>(null);
  const skipBlurSubmitRef = useRef(false);
  
  // Stores
  const { user } = useAuthStore();
  const { logout } = useAuth();
  const { currentSessionId, setCurrentSession, loadMessages } = useChatStore();
  const { reset: resetGeneration } = useGenerationStore();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  
  // Sessions query - only fetch active (non-archived) sessions
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions({ limit: 10, status: 'active' });
  const createSessionMutation = useCreateSession();
  const deleteSessionMutation = useDeleteSession();
  const updateSessionMutation = useUpdateSession();
  const sortedSessions = sessionsData?.data ? sortSidebarSessions(sessionsData.data) : [];

  useEffect(() => {
    if (editingSessionId) {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }
  }, [editingSessionId]);

  const menuItems = [
    { key: 'dashboard', icon: <AppstoreOutlined />, label: 'Home', path: '/dashboard' },
    { key: 'projects', icon: <FileOutlined />, label: 'Projects', path: '/sessions' },
    { key: 'knowledge-base', icon: <FileOutlined />, label: 'Reference Library', path: '/knowledge-base' },
  ];

  const handleNewChat = async () => {
    try {
      const newSession = await createSessionMutation.mutateAsync({
        title: DEFAULT_PRESENTATION_TITLE,
        status: 'active',
      });
      setCurrentSession(newSession.id);
      resetGeneration();
      onNavigate?.();
      navigate('/generate');
    } catch {
      // Error handled by mutation
    }
  };

  const handleSessionClick = (sessionId: string) => {
    setCurrentSession(sessionId);
    loadMessages(sessionId);
    onNavigate?.();
    navigate('/generate');
  };

  const handleRenameStart = (sessionId: string, title: string, topic?: string | null) => {
    setEditingSessionId(sessionId);
    setTitleDraft(getSessionDisplayTitle(title, topic));
  };

  const handleRenameCancel = () => {
    skipBlurSubmitRef.current = true;
    setEditingSessionId(null);
    setTitleDraft('');
  };

  const handleRenameSubmit = async (sessionId: string, currentTitle: string) => {
    const nextTitle = getUpdatedSessionTitle(titleDraft, currentTitle);

    if (!nextTitle || nextTitle === currentTitle.trim()) {
      setEditingSessionId(null);
      setTitleDraft('');
      return;
    }

    try {
      await updateSessionMutation.mutateAsync({
        id: sessionId,
        data: { title: nextTitle },
      });
      setEditingSessionId(null);
      setTitleDraft('');
    } catch {
      setTitleDraft(currentTitle);
    }
  };

  const handleTogglePinned = async (session: typeof sortedSessions[number]) => {
    await updateSessionMutation.mutateAsync({
      id: session.id,
      data: {
        extra_data: togglePinnedExtraData(
          session.extra_data,
          !isSidebarSessionPinned(session)
        ),
      },
    });
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return '';
    }
  };

  const userPanelData = getSidebarUserPanelData(user);

  return (
    <div className="flex flex-col h-full bg-surface-50 border-r border-border/70 text-text-main">
      {/* Logo Area */}
      <div
        className={cn(
          'flex items-center',
          sidebarCollapsed ? 'justify-center px-3 py-4' : 'justify-between gap-3 p-6'
        )}
      >
        {!sidebarCollapsed && (
          <div className="flex items-center gap-3 min-w-0">
            <div className="brand-mark w-8 h-8 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <h1 className="text-base font-bold m-0 leading-tight tracking-tight">SlideGen</h1>
          </div>
        )}
        <Tooltip
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          placement="right"
        >
          <button
            type="button"
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
            className={cn(
              'flex items-center justify-center rounded-lg border border-border/70 bg-surface-50/70 text-text-secondary hover:bg-surface-100 hover:text-text-main transition-colors',
              sidebarCollapsed ? 'w-10 h-10' : 'w-10 h-10 flex-shrink-0'
            )}
          >
            {sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
        </Tooltip>
      </div>

      {/* Primary creation button */}
      <div className={cn(sidebarCollapsed ? 'px-2 mb-4' : 'px-3 mb-4')}>
        <Tooltip title={sidebarCollapsed ? 'New Presentation' : undefined} placement="right">
          <button
            onClick={handleNewChat}
            disabled={createSessionMutation.isPending}
            aria-label="New Presentation"
            className={cn(
              'brand-solid-button flex items-center justify-center rounded-lg text-sm font-semibold transition-all active:scale-[0.98] disabled:opacity-50',
              sidebarCollapsed ? 'w-14 h-11 mx-auto' : 'w-full gap-2 px-4 py-2.5'
            )}
          >
            {createSessionMutation.isPending ? <LoadingOutlined /> : <PlusOutlined />}
            {!sidebarCollapsed && <span>New Presentation</span>}
          </button>
        </Tooltip>
      </div>

      {/* Navigation */}
      <nav className={cn(sidebarCollapsed ? 'px-2 space-y-2' : 'px-3 space-y-1')}>
        {menuItems.map((item) => (
          <Tooltip key={item.key} title={sidebarCollapsed ? item.label : undefined} placement="right">
            <button
              onClick={() => {
                onNavigate?.();
                navigate(item.path);
              }}
              aria-label={item.label}
              className={cn(
                'w-full flex rounded-lg text-sm font-medium transition-all duration-200',
                sidebarCollapsed
                  ? 'h-11 items-center justify-center px-0'
                  : 'items-center gap-3 px-3 py-2.5',
                location.pathname === item.path
                  ? 'bg-brand-surface text-brand-strong border border-brand-border pointer-events-none'
                  : 'text-text-secondary hover:bg-surface-100 hover:text-text-main border border-transparent'
              )}
            >
              {item.icon}
              {!sidebarCollapsed && <span>{item.label}</span>}
            </button>
          </Tooltip>
        ))}
      </nav>

      {/* Recent Sessions */}
      <div className="flex-1 px-3 mt-6 overflow-hidden flex flex-col">
        {!sidebarCollapsed && (
          <>
            <h3 className="text-[11px] font-bold text-text-muted uppercase tracking-[0.18em] mb-3 px-3">
              Recent Projects
            </h3>
            <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar pr-1">
              {sessionsLoading ? (
                <div className="flex justify-center py-4">
                  <Spin size="small" />
                </div>
              ) : !sidebarCollapsed && sortedSessions.length > 0 ? (
                sortedSessions.map((session) => {
                  const isPinned = isSidebarSessionPinned(session);
                  const isEditing = editingSessionId === session.id;
                  const menuItems: MenuProps['items'] = [
                    {
                      key: 'pin',
                      icon: <PushpinOutlined />,
                      label: isPinned ? 'Unpin' : 'Pin',
                      onClick: () => void handleTogglePinned(session),
                    },
                    {
                      key: 'rename',
                      icon: <EditOutlined />,
                      label: 'Rename',
                      onClick: () => handleRenameStart(session.id, session.title, session.topic),
                    },
                    {
                      key: 'delete',
                      icon: <DeleteOutlined />,
                      label: 'Delete',
                      danger: true,
                      onClick: () => {
                        Modal.confirm({
                          title: 'Delete project',
                          content: 'Are you sure you want to delete this presentation project?',
                          okText: 'Delete',
                          cancelText: 'Cancel',
                          okButtonProps: { danger: true },
                          onOk: () =>
                            new Promise<void>((resolve, reject) => {
                              deleteSessionMutation.mutate(session.id, {
                                onSuccess: () => {
                                  if (currentSessionId === session.id) {
                                    setCurrentSession(null);
                                    resetGeneration();
                                  }
                                  resolve();
                                },
                                onError: () => reject(new Error('delete failed')),
                              });
                            }),
                        });
                      },
                    },
                  ];

                  return (
                    <div
                      key={session.id}
                      className={cn(
                        'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all duration-200 group border border-transparent',
                        currentSessionId === session.id
                          ? 'bg-surface-100 text-text-main border-border/70 shadow-sm'
                          : 'text-text-secondary hover:bg-surface-100 hover:text-text-main'
                      )}
                    >
                      {isEditing ? (
                        <div className="flex flex-1 min-w-0 items-center gap-2">
                          <div
                            className={cn(
                              'flex items-center justify-center w-6 h-6 rounded flex-shrink-0 transition-colors',
                              currentSessionId === session.id
                                ? 'text-brand-strong bg-brand-surface'
                                : 'bg-surface-100 group-hover:bg-surface-200'
                            )}
                          >
                            <MessageOutlined className="text-[10px]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <Input
                              ref={titleInputRef}
                              value={titleDraft}
                              maxLength={120}
                              size="small"
                              onChange={(event) => setTitleDraft(event.target.value)}
                              onBlur={() => {
                                if (skipBlurSubmitRef.current) {
                                  skipBlurSubmitRef.current = false;
                                  return;
                                }
                                void handleRenameSubmit(session.id, session.title);
                              }}
                              onKeyDown={(event) => {
                                if (event.nativeEvent.isComposing || event.keyCode === 229) {
                                  return;
                                }

                                if (event.key === 'Enter') {
                                  event.preventDefault();
                                  void handleRenameSubmit(session.id, session.title);
                                }
                                if (event.key === 'Escape') {
                                  event.preventDefault();
                                  handleRenameCancel();
                                }
                              }}
                            />
                            <p className="text-xs text-text-muted m-0">
                              {formatDate(session.update_time)}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleSessionClick(session.id)}
                          aria-current={currentSessionId === session.id ? 'page' : undefined}
                          className="flex flex-1 min-w-0 items-center gap-2 text-left"
                        >
                          <div
                            className={cn(
                              'flex items-center justify-center w-6 h-6 rounded flex-shrink-0 transition-colors',
                              currentSessionId === session.id
                                ? 'text-brand-strong bg-brand-surface'
                                : 'bg-surface-100 group-hover:bg-surface-200'
                            )}
                          >
                            <MessageOutlined className="text-[10px]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 min-w-0">
                              {isPinned ? (
                                <PushpinOutlined className="text-[10px] text-brand-strong flex-shrink-0" />
                              ) : null}
                              <p className="text-sm font-medium truncate m-0 text-text-main group-hover:text-brand-strong transition-colors">
                                {getSessionDisplayTitle(session.title, session.topic)}
                              </p>
                            </div>
                            <p className="text-xs text-text-muted m-0">
                              {formatDate(session.update_time)}
                            </p>
                          </div>
                        </button>
                      )}
                      <Dropdown
                        trigger={['click']}
                        placement="bottomRight"
                        menu={{ items: menuItems }}
                      >
                        <button
                          type="button"
                          onClick={(event) => event.stopPropagation()}
                          className={cn(
                            'p-1 rounded text-text-secondary transition-all flex-shrink-0 hover:bg-surface-200 hover:text-text-main',
                            currentSessionId === session.id || isEditing
                              ? 'opacity-100'
                              : 'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100'
                          )}
                          title="More actions"
                        >
                          <MoreOutlined className="text-sm" />
                        </button>
                      </Dropdown>
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-text-muted text-center py-4">
                  No recent projects
                </p>
              )}
            </div>
          </>
        )}
      </div>

      {/* Settings / User */}
      <div className={cn('border-t border-border/70 mt-auto', sidebarCollapsed ? 'p-2' : 'p-4')}>
        <Tooltip title={sidebarCollapsed ? 'Settings' : undefined} placement="right">
          <button
            onClick={() => {
              onNavigate?.();
              navigate('/settings');
            }}
            aria-label="Settings"
            className={cn(
              'flex text-sm font-medium text-text-secondary hover:text-text-main hover:bg-surface-100 transition-colors',
              sidebarCollapsed
                ? 'w-14 h-11 mx-auto items-center justify-center rounded-lg mb-2'
                : 'w-full items-center gap-3 px-3 py-2 rounded-lg mb-2'
            )}
          >
            <SettingOutlined />
            {!sidebarCollapsed && <span>Settings</span>}
          </button>
        </Tooltip>
        
        <Popover
          trigger="click"
          placement="rightBottom"
          open={userPanelOpen}
          onOpenChange={setUserPanelOpen}
          content={
            <div className="w-72 rounded-2xl bg-surface-50 p-3 text-text-main">
              <div className="flex items-center gap-3 rounded-xl px-2 py-2">
                <div className="brand-mark w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white">
                  {userPanelData.initials}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="m-0 truncate text-sm font-semibold text-text-main">
                    {userPanelData.displayName}
                  </p>
                  <p className="m-0 truncate text-xs text-text-muted">
                    {userPanelData.email}
                  </p>
                </div>
              </div>
              <div className="mt-2 border-t border-border/70 pt-3">
                <Button
                  danger
                  block
                  icon={<LogoutOutlined />}
                  className="!h-10 !rounded-xl"
                  onClick={() => {
                    setUserPanelOpen(false);
                    logout();
                  }}
                >
                  Sign out
                </Button>
              </div>
            </div>
          }
          overlayInnerStyle={{
            padding: 0,
            borderRadius: 16,
          }}
        >
          <button
            type="button"
            aria-label="User menu"
            className={cn(
              'w-full mt-2 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer group border-0 bg-transparent text-left',
              sidebarCollapsed
                ? 'h-11 flex items-center justify-center px-0'
                : 'flex items-center gap-3 px-3 py-2'
            )}
          >
            <div className="brand-mark w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white">
              {userPanelData.initials}
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-main truncate group-hover:text-brand-strong transition-colors">
                  {userPanelData.displayName}
                </p>
                <p className="text-xs text-text-muted truncate">{userPanelData.email}</p>
              </div>
            )}
          </button>
        </Popover>
      </div>
    </div>
  );
};
