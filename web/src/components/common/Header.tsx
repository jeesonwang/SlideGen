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
  BgColorsOutlined,
  SunOutlined,
  MoonOutlined,
  DesktopOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useUIStore } from '../../store/uiStore';
import { getThemeModeLabel, THEME_MODE_OPTIONS, type ThemeMode } from '../../theme/themeMode';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { sidebarCollapsed, toggleSidebar, themeMode, setThemeMode } = useUIStore();

  const getThemeIcon = (mode: ThemeMode) => {
    switch (mode) {
      case 'light':
        return <SunOutlined />;
      case 'dark':
        return <MoonOutlined />;
      default:
        return <DesktopOutlined />;
    }
  };

  const themeMenuItems: MenuProps['items'] = THEME_MODE_OPTIONS.map((option) => ({
    key: option.value,
    icon: getThemeIcon(option.value),
    label: option.label,
    onClick: () => setThemeMode(option.value),
  }));

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
    <AntHeader className="!px-8 !py-0 !bg-surface-50/80 backdrop-blur-md flex items-center justify-between border-b !border-border/70 sticky top-0 z-20 h-20">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="w-11 h-11 rounded-lg hover:bg-surface-100 flex items-center justify-center transition-all duration-200 cursor-pointer text-text-secondary hover:text-text-main"
          aria-label="Toggle sidebar"
        >
          {sidebarCollapsed ? (
            <MenuUnfoldOutlined className="text-lg" />
          ) : (
            <MenuFoldOutlined className="text-lg" />
          )}
        </button>
      </div>

      <div className="flex items-center gap-3">
        <Dropdown
          menu={{
            items: themeMenuItems,
            selectable: true,
            selectedKeys: [themeMode],
          }}
          placement="bottomRight"
          trigger={['click']}
        >
          <button
            className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-surface-100 cursor-pointer transition-all duration-200 border border-border/70 bg-surface-50/70 text-text-main"
            aria-label="Theme menu"
            aria-haspopup="true"
          >
            <BgColorsOutlined className="text-brand-strong" />
            <span className="hidden sm:inline text-sm font-medium">
              {getThemeModeLabel(themeMode)}
            </span>
          </button>
        </Dropdown>

        <Dropdown
          menu={{ items: userMenuItems }}
          placement="bottomRight"
          trigger={['click']}
        >
          <button
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-100 cursor-pointer transition-all duration-200 border-0 bg-transparent"
            aria-label="User menu"
            aria-haspopup="true"
          >
            <Space size={12}>
              <div className="text-right hidden sm:block">
                <Text className="block text-sm font-medium !text-text-main">
                  {user?.username || 'User'}
                </Text>
                <Text className="block text-xs !text-text-secondary">
                  {user?.email}
                </Text>
              </div>
              <Avatar
                size={40}
                className="!bg-gradient-to-br !from-primary-600 !to-primary-700"
                icon={<UserOutlined />}
              />
            </Space>
          </button>
        </Dropdown>
      </div>
    </AntHeader>
  );
};
