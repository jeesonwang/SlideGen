/**
 * User-related React Query hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { userApi } from '../api/endpoints/user';
import { useAuthStore } from '../store/authStore';
import type { UserUpdate, UpdatePassword } from '../api/types/auth.types';

/**
 * Get current user information
 */
export const useUser = () => {
  return useQuery({
    queryKey: ['user', 'me'],
    queryFn: userApi.getMe,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
};

/**
 * Update current user information
 */
export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();

  return useMutation({
    mutationFn: (data: UserUpdate) => userApi.updateMe(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] });
      setUser(data);
      message.success('Profile updated successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to update profile');
    },
  });
};

/**
 * Update user password
 */
export const useUpdatePassword = () => {
  return useMutation({
    mutationFn: (data: UpdatePassword) => userApi.updatePassword(data),
    onSuccess: () => {
      message.success('Password updated successfully');
    },
    onError: (error: any) => {
      message.error(error?.detail || 'Failed to update password');
    },
  });
};
