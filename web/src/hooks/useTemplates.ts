import { useQuery } from '@tanstack/react-query';
import { slidegenApi } from '../api/endpoints/slidegen';
import type { Template } from '../api/types/slidegen.types';

export const useTemplates = () => {
  return useQuery<Template[]>({
    queryKey: ['templates'],
    queryFn: slidegenApi.getTemplates,
  });
};
