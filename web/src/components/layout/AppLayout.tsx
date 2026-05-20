import { Button, Drawer, Grid, Layout } from 'antd';
import { MenuUnfoldOutlined } from '@ant-design/icons';
import { Sidebar } from '../common/Sidebar';
import { Outlet } from 'react-router-dom';
import { useUIStore } from '../../store/uiStore';

const { Content, Sider } = Layout;
const { useBreakpoint } = Grid;

interface RouteScopedLayoutProps {
  sidebarCollapsed: boolean;
}

const RouteScopedLayout = ({
  sidebarCollapsed,
}: RouteScopedLayoutProps) => {
  const { setSidebarCollapsed } = useUIStore();
  const screens = useBreakpoint();
  const isMobile = !screens.lg;

  return (
    <>
      <Layout className="workbench-app h-screen h-dvh w-screen overflow-hidden bg-background flex flex-row">
        {!isMobile && (
          <Sider
            width={260}
            collapsed={sidebarCollapsed}
            collapsedWidth={96}
            className="!bg-transparent !border-r-0"
            trigger={null}
          >
            <Sidebar />
          </Sider>
        )}

        <Content className="flex-1 h-full relative overflow-hidden flex flex-col min-w-0">
          {isMobile && sidebarCollapsed && (
            <Button
              type="default"
              shape="circle"
              icon={<MenuUnfoldOutlined />}
              aria-label="Open sidebar"
              onClick={() => setSidebarCollapsed(false)}
              className="!absolute !left-4 !top-4 !z-30 !h-11 !w-11 !min-w-0 !border-border/70 !bg-surface-50/92 !text-text-main !shadow-soft lg:!hidden"
            />
          )}
          <Outlet />
        </Content>
      </Layout>

      {isMobile && (
        <Drawer
          placement="left"
          open={!sidebarCollapsed}
          onClose={() => setSidebarCollapsed(true)}
          closable={false}
          width={280}
          className="[&_.ant-drawer-content]:!bg-transparent"
          styles={{
            body: { padding: 0, background: 'transparent' },
          }}
        >
          <Sidebar onNavigate={() => setSidebarCollapsed(true)} />
        </Drawer>
      )}
    </>
  );
};

export const AppLayout = () => {
  const { sidebarCollapsed } = useUIStore();

  return <RouteScopedLayout sidebarCollapsed={sidebarCollapsed} />;
};
