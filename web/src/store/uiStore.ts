/**
 * UI state store using Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ThemeMode } from '../theme/themeMode';

interface UIState {
  sidebarCollapsed: boolean;
  themeMode: ThemeMode;

  // Actions
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setThemeMode: (themeMode: ThemeMode) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      themeMode: 'system',

      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      setSidebarCollapsed: (collapsed: boolean) => {
        set({ sidebarCollapsed: collapsed });
      },

      setThemeMode: (themeMode: ThemeMode) => {
        set({ themeMode });
      },
    }),
    {
      name: 'ui-storage',
    }
  )
);
