/**
 * Main App component with providers
 */

import { Suspense } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, Spin } from 'antd';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { router } from './router';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          theme={{
            token: {
              colorPrimary: '#2563EB',
              colorSuccess: '#16A34A',
              colorWarning: '#F59E0B',
              colorError: '#EF4444',
              colorInfo: '#2563EB',
              borderRadius: 8,
              fontFamily: "'Open Sans', -apple-system, BlinkMacSystemFont, sans-serif",
              fontSize: 14,
            },
            components: {
              Button: {
                primaryShadow: '0 2px 8px rgba(37, 99, 235, 0.15)',
                controlHeight: 40,
                controlHeightLG: 48,
                borderRadius: 8,
                borderRadiusLG: 10,
              },
              Card: {
                borderRadiusLG: 12,
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              },
              Input: {
                controlHeight: 40,
                controlHeightLG: 48,
                borderRadius: 8,
                borderRadiusLG: 10,
              },
              Select: {
                controlHeight: 40,
                controlHeightLG: 48,
                borderRadius: 8,
                borderRadiusLG: 10,
              },
              Menu: {
                itemBorderRadius: 8,
                itemMarginBlock: 4,
                itemMarginInline: 8,
              },
            },
          }}
        >
          <Suspense
            fallback={
              <div className="flex justify-center items-center h-screen bg-secondary-50">
                <div className="text-center">
                  <Spin size="large" />
                  <p className="mt-4 text-secondary-600 font-medium">Loading...</p>
                </div>
              </div>
            }
          >
            <RouterProvider router={router} />
          </Suspense>
        </ConfigProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
