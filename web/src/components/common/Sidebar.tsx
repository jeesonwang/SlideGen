/**
 * Sidebar component with navigation menu
 */

import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUIStore } from '../../store/uiStore';

const { Sider } = Layout;

type MenuItem = Required<MenuProps>['items'][number];

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarCollapsed } = useUIStore();

  const menuItems: MenuItem[] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => navigate('/dashboard'),
    },
    {
      key: '/generate',
      icon: <ThunderboltOutlined />,
      label: 'Generate PPT',
      onClick: () => navigate('/generate'),
    },
    {
      key: 'config',
      icon: <SettingOutlined />,
      label: 'Configuration',
      children: [
        {
          key: '/config/llm',
          label: 'LLM Config',
          onClick: () => navigate('/config/llm'),
        },
        {
          key: '/config/embedding',
          label: 'Embedding Config',
          onClick: () => navigate('/config/embedding'),
        },
      ],
    },
    {
      key: '/sessions',
      icon: <FileTextOutlined />,
      label: 'Sessions',
      onClick: () => navigate('/sessions'),
    },
    {
      key: '/knowledge-base',
      icon: <DatabaseOutlined />,
      label: 'Knowledge Base',
      onClick: () => navigate('/knowledge-base'),
    },
  ];

  // Determine which menu item should be selected based on current path
  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.startsWith('/config/')) {
      return [path];
    }
    return [path];
  };

  // Determine which submenu should be open
  const getOpenKeys = () => {
    if (location.pathname.startsWith('/config/')) {
      return ['config'];
    }
    return [];
  };

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={sidebarCollapsed}
      width={260}
      collapsedWidth={80}
      className="!bg-white border-r border-secondary-200 shadow-soft"
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'sticky',
        left: 0,
        top: 0,
        bottom: 0,
      }}
      theme="light"
    >
      {/* Logo Section */}
      <div className="h-20 flex items-center justify-center px-6 border-b border-secondary-100">
        {sidebarCollapsed ? (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center shadow-soft">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="SlideGen logo">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center shadow-soft">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="SlideGen logo">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
              </svg>
            </div>
            <span className="text-xl font-heading font-semibold text-gradient">SlideGen</span>
          </div>
        )}
      </div>

      {/* Navigation Menu */}
      <div className="py-4">
        <Menu
          mode="inline"
          selectedKeys={getSelectedKeys()}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          className="!border-0 !bg-transparent"
          style={{
            fontSize: '14px',
            fontWeight: 500,
          }}
        />
      </div>
    </Sider>
  );
};
