/**
 * Main App component with providers
 */

import { Suspense, useEffect, useState } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, Spin } from 'antd';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { router } from './router';
import { useUIStore } from './store/uiStore';
import { resolveThemeMode } from './theme/themeMode';
import { getAntdThemeConfig } from './theme/tokens';

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

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return undefined;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (event: MediaQueryListEvent) => {
      setSystemPrefersDark(event.matches);
    };

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
      theme={getAntdThemeConfig(resolvedTheme)}
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
