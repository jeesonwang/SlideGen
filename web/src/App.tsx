/**
 * Main App component with providers
 */

import { Suspense, useEffect, useState } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, Spin, theme } from 'antd';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { router } from './router';
import { useUIStore } from './store/uiStore';
import { resolveThemeMode } from './theme/themeMode';

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

const getSystemPrefersDark = (): boolean =>
  typeof window !== 'undefined' &&
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-color-scheme: dark)').matches;

const AppShell = () => {
  const themeMode = useUIStore((state) => state.themeMode);
  const [systemPrefersDark, setSystemPrefersDark] = useState<boolean>(getSystemPrefersDark);
  const resolvedTheme = resolveThemeMode(themeMode, systemPrefersDark);
  const isDark = resolvedTheme === 'dark';

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return undefined;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (event: MediaQueryListEvent) => {
      setSystemPrefersDark(event.matches);
    };

    setSystemPrefersDark(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#2563EB',
          colorSuccess: '#16A34A',
          colorWarning: '#F59E0B',
          colorError: '#EF4444',
          colorInfo: '#2563EB',
          colorBgBase: isDark ? '#0B0F19' : '#F3F7FC',
          colorBgContainer: isDark ? 'rgba(24, 28, 41, 0.82)' : 'rgba(255, 255, 255, 0.92)',
          colorBgElevated: isDark ? 'rgba(24, 28, 41, 0.96)' : 'rgba(255, 255, 255, 0.98)',
          colorText: isDark ? '#F8FAFC' : '#0F172A',
          colorTextSecondary: isDark ? '#94A3B8' : '#475569',
          colorBorder: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(148, 163, 184, 0.28)',
          borderRadius: 8,
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
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
            boxShadow: isDark
              ? '0 8px 24px rgba(2, 6, 23, 0.18)'
              : '0 10px 28px rgba(15, 23, 42, 0.08)',
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
            optionSelectedBg: isDark ? 'rgba(37, 99, 235, 0.2)' : 'rgba(37, 99, 235, 0.12)',
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
          <div className="flex justify-center items-center h-screen bg-background">
            <div className="text-center">
              <Spin size="large" />
              <p className="mt-4 text-text-secondary font-medium">Loading...</p>
            </div>
          </div>
        }
      >
        <RouterProvider router={router} />
      </Suspense>
    </ConfigProvider>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppShell />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
