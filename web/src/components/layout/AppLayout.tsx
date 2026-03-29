import { useState } from 'react';
import { Button, Drawer, Grid, Layout } from 'antd';
import { MenuUnfoldOutlined } from '@ant-design/icons';
import { Sidebar } from '../common/Sidebar';
import { ConfigurationPanel } from '../config/ConfigurationPanel';
import { Outlet, useLocation } from 'react-router-dom';
import { LayoutContext } from '../../context/LayoutContext';
import { getRightPanelVisibility } from './rightPanelVisibility';
import { getDefaultRightPanelCollapsed } from './rightPanelPolicy';
import { useUIStore } from '../../store/uiStore';

const { Content, Sider } = Layout;
const { useBreakpoint } = Grid;

interface RouteScopedLayoutProps {
  pathname: string;
  sidebarCollapsed: boolean;
}

const RouteScopedLayout = ({
  pathname,
  sidebarCollapsed,
}: RouteScopedLayoutProps) => {
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(() =>
    getDefaultRightPanelCollapsed(pathname)
  );
  const { setSidebarCollapsed } = useUIStore();
  const screens = useBreakpoint();
  const isMobile = !screens.lg;
  const { showPanel } = getRightPanelVisibility(rightPanelCollapsed);

  return (
    <LayoutContext.Provider value={{ rightPanelCollapsed, setRightPanelCollapsed }}>
      <Layout className="h-screen w-screen overflow-hidden bg-background flex flex-row">
        {/* Left Sidebar */}
        {!isMobile && (
          <Sider
            width={260}
            collapsed={sidebarCollapsed}
            collapsedWidth={80}
            className="!bg-surface-50 border-r border-border"
            trigger={null}
          >
            <Sidebar />
          </Sider>
        )}

        {/* Main Content Area (Chat/Dashboard) */}
        <Content className="flex-1 h-full relative overflow-hidden flex flex-col min-w-0">
          {isMobile && sidebarCollapsed && (
            <Button
              type="default"
              shape="circle"
              icon={<MenuUnfoldOutlined />}
              aria-label="Open sidebar"
              onClick={() => setSidebarCollapsed(false)}
              className="!absolute !left-4 !top-4 !z-30 !h-11 !w-11 !min-w-0 !border-border/70 !bg-surface-50/90 !text-text-main !shadow-soft lg:!hidden"
            />
          )}
          <Outlet />
        </Content>

        {/* Right Configuration Panel */}
        {!isMobile && showPanel && (
          <Sider 
            width={320} 
            className="!bg-surface-50 border-l border-border h-full"
            trigger={null}
          >
            <ConfigurationPanel onCollapse={() => setRightPanelCollapsed(true)} />
          </Sider>
        )}
      </Layout>

      {isMobile && (
        <Drawer
          placement="left"
          open={!sidebarCollapsed}
          onClose={() => setSidebarCollapsed(true)}
          closable={false}
          width={280}
          className="[&_.ant-drawer-content]:!bg-surface-50"
          styles={{
            body: { padding: 0 },
          }}
        >
          <Sidebar onNavigate={() => setSidebarCollapsed(true)} />
        </Drawer>
      )}

      {isMobile && showPanel && (
        <Drawer
          placement="right"
          open={!rightPanelCollapsed}
          onClose={() => setRightPanelCollapsed(true)}
          closable={false}
          width={320}
          className="[&_.ant-drawer-content]:!bg-surface-50"
          styles={{
            body: { padding: 0 },
          }}
        >
          <ConfigurationPanel onCollapse={() => setRightPanelCollapsed(true)} />
        </Drawer>
      )}
    </LayoutContext.Provider>
  );
};

export const AppLayout = () => {
  const location = useLocation();
  const { sidebarCollapsed } = useUIStore();

  return (
    <RouteScopedLayout
      key={location.pathname}
      pathname={location.pathname}
      sidebarCollapsed={sidebarCollapsed}
    />
  );
};
