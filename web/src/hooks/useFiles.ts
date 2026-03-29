/**
 * React Query hooks for files
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { filesApi } from '../api/endpoints/files';
import { message } from 'antd';
import { getErrorDetail } from '../utils/errorDetail';

export const useFiles = (params?: {
  skip?: number;
  limit?: number;
  session_id?: string;
}) => {
  return useQuery({
    queryKey: ['files', params],
    queryFn: () => filesApi.list(params),
  });
};

export const useUploadFile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, sessionId }: { file: File; sessionId: string }) =>
      filesApi.upload(file, sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      message.success('File uploaded successfully');
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to upload file'));
    },
  });
};

export const useUploadMultipleFiles = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ files, sessionId }: { files: File[]; sessionId: string }) =>
      filesApi.uploadMultiple(files, sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      message.success('Files uploaded successfully');
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to upload files'));
    },
  });
};

export const useDeleteFile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => filesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      message.success('File deleted successfully');
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to delete file'));
    },
  });
};

export const useDownloadFile = () => {
  return useMutation({
    mutationFn: async ({ id, filename }: { id: string; filename: string }) => {
      const blob = await filesApi.download(id);

      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
    onError: (error: unknown) => {
      message.error(getErrorDetail(error, 'Failed to download file'));
    },
  });
};
