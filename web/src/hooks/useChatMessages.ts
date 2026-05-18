import { useMutation, useQueryClient } from '@tanstack/react-query';
import { chatMessagesApi } from '../api/endpoints/chatMessages';
import type { ChatMessageCreate } from '../api/types/chatMessage.types';
import { getErrorDetail } from '../utils/errorDetail';

export const useAddChatMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      message,
    }: {
      sessionId: string;
      message: ChatMessageCreate;
    }) => chatMessagesApi.addMessage(sessionId, message),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['sessions', variables.sessionId] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
    onError: (error: unknown) => {
      console.error('Failed to save message:', getErrorDetail(error, 'Failed to save message'));
    },
  });
};
