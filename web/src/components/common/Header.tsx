/**
 * Header component with user menu and breadcrumbs
 */

import { Layout, Dropdown, Avatar, Space, Typography } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useUIStore } from '../../store/uiStore';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'user-info',
      label: (
        <div className="py-1">
          <Text strong>{user?.username || user?.email}</Text>
          <br />
          <Text type="secondary" className="text-xs">
            {user?.email}
          </Text>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'profile',
      icon: <SettingOutlined />,
      label: 'Profile Settings',
      onClick: () => navigate('/profile'),
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: logout,
      danger: true,
    },
  ];

  return (
    <AntHeader className="!px-8 !py-0 !bg-white/80 backdrop-blur-md flex items-center justify-between border-b border-secondary-100 sticky top-0 z-20 shadow-soft h-20">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="w-10 h-10 rounded-lg hover:bg-secondary-100 flex items-center justify-center transition-all duration-200 cursor-pointer"
          aria-label="Toggle sidebar"
        >
          {sidebarCollapsed ? (
            <MenuUnfoldOutlined className="text-lg text-secondary-600" />
          ) : (
            <MenuFoldOutlined className="text-lg text-secondary-600" />
          )}
        </button>
      </div>

      <Dropdown
        menu={{ items: userMenuItems }}
        placement="bottomRight"
        trigger={['click']}
      >
        <button
          className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-secondary-50 cursor-pointer transition-all duration-200 border-0 bg-transparent"
          aria-label="User menu"
          aria-haspopup="true"
        >
          <Space size={12}>
            <div className="text-right hidden sm:block">
              <Text className="block text-sm font-medium text-secondary-900">
                {user?.username || 'User'}
              </Text>
              <Text className="block text-xs text-secondary-500">
                {user?.email}
              </Text>
            </div>
            <Avatar
              size={40}
              className="!bg-gradient-to-br !from-primary-600 !to-primary-700 shadow-soft"
              icon={<UserOutlined />}
            />
          </Space>
        </button>
      </Dropdown>
    </AntHeader>
  );
};
