import { useEffect, useState } from 'react';
import { Layout } from 'antd';
import { Sidebar } from '../common/Sidebar';
import { ConfigurationPanel } from '../config/ConfigurationPanel';
import { Outlet, useLocation } from 'react-router-dom';
import { LayoutContext } from '../../context/LayoutContext';
import { getRightPanelVisibility } from './rightPanelVisibility';
import { getDefaultRightPanelCollapsed } from './rightPanelPolicy';
import { useUIStore } from '../../store/uiStore';

const { Content, Sider } = Layout;

export const AppLayout = () => {
  const location = useLocation();
  const { sidebarCollapsed } = useUIStore();
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(() =>
    getDefaultRightPanelCollapsed(location.pathname)
  );

  useEffect(() => {
    setRightPanelCollapsed(getDefaultRightPanelCollapsed(location.pathname));
  }, [location.pathname]);

  const { showPanel } = getRightPanelVisibility(rightPanelCollapsed);

  return (
    <LayoutContext.Provider value={{ rightPanelCollapsed, setRightPanelCollapsed }}>
      <Layout className="h-screen w-screen overflow-hidden bg-background flex flex-row">
        {/* Left Sidebar */}
        <Sider
          width={260}
          collapsed={sidebarCollapsed}
          collapsedWidth={80}
          className="!bg-surface-50 border-r border-border"
          trigger={null}
        >
          <Sidebar />
        </Sider>

        {/* Main Content Area (Chat/Dashboard) */}
        <Content className="flex-1 h-full relative overflow-hidden flex flex-col min-w-0">
          <Outlet />
        </Content>

        {/* Right Configuration Panel */}
        {showPanel && (
          <Sider 
            width={320} 
            className="!bg-surface-50 border-l border-border h-full"
            trigger={null}
          >
            <ConfigurationPanel onCollapse={() => setRightPanelCollapsed(true)} />
          </Sider>
        )}
      </Layout>
    </LayoutContext.Provider>
  );
};
