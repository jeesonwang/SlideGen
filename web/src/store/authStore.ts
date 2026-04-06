/**
 * Authentication store using Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserPublic } from '../api/types/auth.types';

interface AuthState {
  token: string | null;
  user: UserPublic | null;
  isAuthenticated: boolean;

  // Actions
  setToken: (token: string) => void;
  setUser: (user: UserPublic) => void;
  login: (token: string, user: UserPublic) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      setToken: (token: string) => {
        set({ token, isAuthenticated: true });
      },

      setUser: (user: UserPublic) => {
        set({ user });
      },

      login: (token: string, user: UserPublic) => {
        set({ token, user, isAuthenticated: true });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
