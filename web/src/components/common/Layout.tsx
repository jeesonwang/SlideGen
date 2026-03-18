/**
 * Main Layout component with Header and Sidebar
 */

import { Layout as AntLayout } from 'antd';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

const { Content } = AntLayout;

export const Layout: React.FC = () => {
  return (
    <AntLayout className="min-h-screen bg-background">
      <Sidebar />
      <AntLayout className="!bg-transparent">
        <Header />
        <Content className="p-6 sm:p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  );
};
