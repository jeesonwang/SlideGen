/**
 * Generation workflow state store using Zustand
 */

import { create } from 'zustand';
import type { GenerateMarkdownRequest } from '../api/types/slidegen.types';

type GenerationStep = 'configure' | 'generating' | 'editing';

interface GenerationState {
  currentStep: GenerationStep;
  markdownContent: string;
  selectedFiles: string[];
  generationParams: Partial<GenerateMarkdownRequest> | null;

  // Actions
  setStep: (step: GenerationStep) => void;
  setMarkdownContent: (content: string) => void;
  updateMarkdownContent: (content: string) => void;
  setSelectedFiles: (files: string[]) => void;
  setGenerationParams: (params: Partial<GenerateMarkdownRequest>) => void;
  reset: () => void;
}

const initialState = {
  currentStep: 'configure' as GenerationStep,
  markdownContent: '',
  selectedFiles: [],
  generationParams: null,
};

export const useGenerationStore = create<GenerationState>((set) => ({
  ...initialState,

  setStep: (step: GenerationStep) => {
    set({ currentStep: step });
  },

  setMarkdownContent: (content: string) => {
    set({ markdownContent: content });
  },

  updateMarkdownContent: (content: string) => {
    set({ markdownContent: content });
  },

  setSelectedFiles: (files: string[]) => {
    set({ selectedFiles: files });
  },

  setGenerationParams: (params: Partial<GenerateMarkdownRequest>) => {
    set({ generationParams: params });
  },

  reset: () => {
    set(initialState);
  },
}));
