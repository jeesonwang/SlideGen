/**
 * Authentication hook using React Query
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/endpoints/auth';
import { useAuthStore } from '../store/authStore';
import type { LoginRequest, UserRegister } from '../api/types/auth.types';

export const useAuth = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { login: setAuthState, logout: clearAuthState, user } = useAuthStore();

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const tokenData = await authApi.login(credentials);

      // Save token to localStorage immediately so testToken can use it
      localStorage.setItem('access_token', tokenData.access_token);

      const userData = await authApi.testToken();
      return { token: tokenData.access_token, user: userData };
    },
    onSuccess: ({ token, user }) => {
      setAuthState(token, user);
      navigate('/dashboard');
    },
  });

  // Signup mutation
  const signupMutation = useMutation({
    mutationFn: async (userData: UserRegister) => {
      return await authApi.signup(userData);
    },
    onSuccess: () => {
      navigate('/login');
    },
  });

  // Logout function
  const logout = () => {
    clearAuthState();
    queryClient.clear();
    navigate('/login');
  };

  // Test token query (for initial auth check)
  const { data: currentUser, isLoading: isCheckingAuth } = useQuery({
    queryKey: ['auth', 'test-token'],
    queryFn: authApi.testToken,
    enabled: !!useAuthStore.getState().token,
    retry: false,
    staleTime: Infinity,
  });

  return {
    user: currentUser || user,
    isAuthenticated: useAuthStore((state) => state.isAuthenticated),
    isCheckingAuth,
    login: loginMutation.mutateAsync,
    signup: signupMutation.mutateAsync,
    logout,
    loginError: loginMutation.error,
    signupError: signupMutation.error,
    isLoggingIn: loginMutation.isPending,
    isSigningUp: signupMutation.isPending,
  };
};
