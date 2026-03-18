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
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { Spin, Dropdown, Input, Modal, Popover, Button } from 'antd';
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
import { getUpdatedSessionTitle } from '../chat/chatSessionTitle';
import {
  isSidebarSessionPinned,
  sortSidebarSessions,
  togglePinnedExtraData,
} from './sidebarSessionList';
import { getSidebarUserPanelData } from './sidebarUserPanel';

export const Sidebar = () => {
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
    { key: 'dashboard', icon: <AppstoreOutlined />, label: 'Dashboard', path: '/dashboard' },
    { key: 'new', icon: <MessageOutlined />, label: 'New Presentation', path: '/generate' },
    { key: 'projects', icon: <FileOutlined />, label: 'Projects', path: '/sessions' },
  ];

  const handleNewChat = async () => {
    try {
      const newSession = await createSessionMutation.mutateAsync({
        title: 'New Presentation',
        status: 'active',
      });
      setCurrentSession(newSession.id);
      resetGeneration();
      navigate('/generate');
    } catch {
      // Error handled by mutation
    }
  };

  const handleSessionClick = (sessionId: string) => {
    setCurrentSession(sessionId);
    loadMessages(sessionId);
    navigate('/generate');
  };

  const handleRenameStart = (sessionId: string, title: string) => {
    setEditingSessionId(sessionId);
    setTitleDraft(title);
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
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary-gradient flex items-center justify-center shadow-glow">
          <span className="text-white font-bold text-lg">S</span>
        </div>
        <div>
          <h1 className="text-base font-bold m-0 leading-tight tracking-tight">AI PPT Gen</h1>
          <p className="text-[10px] text-primary-400 font-medium tracking-wider m-0">ENTERPRISE</p>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-3 mb-4">
        <button
          onClick={handleNewChat}
          disabled={createSessionMutation.isPending}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-primary-gradient hover:opacity-90 text-white text-sm font-semibold shadow-glow transition-all active:scale-[0.98] disabled:opacity-50"
        >
          {createSessionMutation.isPending ? <LoadingOutlined /> : <PlusOutlined />}
          <span>New Chat</span>
        </button>
      </div>

      {/* Navigation */}
      <nav className="px-3 space-y-1">
        {menuItems.map((item) => (
          <button
            key={item.key}
            onClick={() => navigate(item.path)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
              location.pathname === item.path
                ? "bg-primary-500/10 text-primary-400 border border-primary-500/20 pointer-events-none"
                : "text-text-secondary hover:bg-surface-100 hover:text-text-main"
            )}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Recent Sessions */}
      <div className="flex-1 px-3 mt-6 overflow-hidden flex flex-col">
        <h3 className="text-[11px] font-bold text-text-muted uppercase tracking-[0.18em] mb-3 px-3">
          Recent Chats
        </h3>
        <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar pr-1">
          {sessionsLoading ? (
            <div className="flex justify-center py-4">
              <Spin size="small" />
            </div>
          ) : sortedSessions.length > 0 ? (
            sortedSessions.map((session) => {
              const isPinned = isSidebarSessionPinned(session);
              const isEditing = editingSessionId === session.id;
              const menuItems: MenuProps['items'] = [
                {
                  key: 'pin',
                  icon: <PushpinOutlined />,
                  label: isPinned ? '取消固定' : '固定',
                  onClick: () => void handleTogglePinned(session),
                },
                {
                  key: 'rename',
                  icon: <EditOutlined />,
                  label: '重命名',
                  onClick: () => handleRenameStart(session.id, session.title),
                },
                {
                  key: 'delete',
                  icon: <DeleteOutlined />,
                  label: '删除',
                  danger: true,
                  onClick: () => {
                    Modal.confirm({
                      title: '删除对话',
                      content: '确定要删除这个对话吗？',
                      okText: '删除',
                      cancelText: '取消',
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
                onClick={() => {
                  if (!isEditing) {
                    handleSessionClick(session.id);
                  }
                }}
                className={cn(
                  "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all duration-200 group border border-transparent cursor-pointer",
                  currentSessionId === session.id
                    ? "bg-surface-100 text-text-main border-border/70 shadow-sm"
                    : "text-text-secondary hover:bg-surface-100 hover:text-text-main"
                )}
              >
                <div className={cn(
                  "flex items-center justify-center w-6 h-6 rounded flex-shrink-0 transition-colors",
                  currentSessionId === session.id ? "text-primary-400 bg-primary-500/10" : "bg-surface-100 group-hover:bg-surface-200"
                )}>
                  <MessageOutlined className="text-[10px]" />
                </div>
                <div className="flex-1 min-w-0">
                  {isEditing ? (
                    <Input
                      ref={titleInputRef}
                      value={titleDraft}
                      maxLength={120}
                      size="small"
                      onClick={(event) => event.stopPropagation()}
                      onChange={(event) => setTitleDraft(event.target.value)}
                      onBlur={() => {
                        if (skipBlurSubmitRef.current) {
                          skipBlurSubmitRef.current = false;
                          return;
                        }
                        void handleRenameSubmit(session.id, session.title);
                      }}
                      onKeyDown={(event) => {
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
                  ) : (
                    <div className="flex items-center gap-1.5 min-w-0">
                      {isPinned ? (
                        <PushpinOutlined className="text-[10px] text-primary-400 flex-shrink-0" />
                      ) : null}
                      <p className="text-sm font-medium truncate m-0 text-text-main group-hover:text-primary-300 transition-colors">
                        {session.title}
                      </p>
                    </div>
                  )}
                  <p className="text-xs text-text-muted m-0">
                    {formatDate(session.update_time)}
                  </p>
                </div>
                <Dropdown
                  trigger={['click']}
                  placement="bottomRight"
                  menu={{ items: menuItems }}
                >
                  <button
                    onClick={(event) => event.stopPropagation()}
                    className={cn(
                      "p-1 rounded text-text-secondary transition-all flex-shrink-0 hover:bg-surface-200 hover:text-text-main",
                      currentSessionId === session.id || isEditing
                        ? "opacity-100"
                        : "opacity-0 group-hover:opacity-100"
                    )}
                    title="更多操作"
                  >
                    <MoreOutlined className="text-sm" />
                  </button>
                </Dropdown>
              </div>
              );
            })
          ) : (
            <p className="text-sm text-text-muted text-center py-4">
              No recent chats
            </p>
          )}
        </div>
      </div>

      {/* Settings / User */}
      <div className="p-4 border-t border-border/70 mt-auto">
        <button 
          onClick={() => navigate('/settings')}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-text-secondary hover:text-text-main hover:bg-surface-100 transition-colors mb-2"
        >
          <SettingOutlined />
          <span>Settings</span>
        </button>
        
        <Popover
          trigger="click"
          placement="topLeft"
          open={userPanelOpen}
          onOpenChange={setUserPanelOpen}
          content={
            <div className="w-72 rounded-2xl bg-surface-50 p-3 text-text-main">
              <div className="flex items-center gap-3 rounded-xl px-2 py-2">
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-accent-purple to-primary-600 flex items-center justify-center text-sm font-bold text-white shadow-glow">
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
                  退出登录
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
            className="w-full flex items-center gap-3 px-3 py-2 mt-2 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer group border-0 bg-transparent text-left"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-accent-purple to-primary-600 flex items-center justify-center text-xs font-bold text-white shadow-glow">
              {userPanelData.initials}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-main truncate group-hover:text-primary-300 transition-colors">
                {userPanelData.displayName}
              </p>
              <p className="text-xs text-text-muted truncate">{userPanelData.email}</p>
            </div>
          </button>
        </Popover>
      </div>
    </div>
  );
};
