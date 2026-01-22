/**
 * Application routing configuration
 */

import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { Layout } from './components/common/Layout';

// Lazy load pages for code splitting
import { lazy } from 'react';

const LoginPage = lazy(() =>
  import('./pages/auth/LoginPage').then((m) => ({ default: m.LoginPage }))
);
const SignupPage = lazy(() =>
  import('./pages/auth/SignupPage').then((m) => ({ default: m.SignupPage }))
);
const DashboardPage = lazy(() =>
  import('./pages/dashboard/DashboardPage').then((m) => ({
    default: m.DashboardPage,
  }))
);
const LLMConfigPage = lazy(() =>
  import('./pages/config/LLMConfigPage').then((m) => ({
    default: m.LLMConfigPage,
  }))
);
const EmbeddingConfigPage = lazy(() =>
  import('./pages/config/EmbeddingConfigPage').then((m) => ({
    default: m.EmbeddingConfigPage,
  }))
);
const SessionsPage = lazy(() =>
  import('./pages/sessions/SessionsPage').then((m) => ({
    default: m.SessionsPage,
  }))
);
const FilesPage = lazy(() =>
  import('./pages/files/FilesPage').then((m) => ({ default: m.FilesPage }))
);
const GenerationPage = lazy(() =>
  import('./pages/generation/GenerationPage').then((m) => ({
    default: m.GenerationPage,
  }))
);
const ProfilePage = lazy(() =>
  import('./pages/profile/ProfilePage').then((m) => ({
    default: m.ProfilePage,
  }))
);
const NotFoundPage = lazy(() =>
  import('./pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage }))
);

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/signup',
    element: <SignupPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'config/llm',
        element: <LLMConfigPage />,
      },
      {
        path: 'config/embedding',
        element: <EmbeddingConfigPage />,
      },
      {
        path: 'sessions',
        element: <SessionsPage />,
      },
      {
        path: 'knowledge-base',
        element: <FilesPage />,
      },
      {
        path: 'generate',
        element: <GenerationPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
