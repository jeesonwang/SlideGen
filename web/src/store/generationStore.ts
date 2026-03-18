/**
 * Generation workflow state store using Zustand
 * Extended with configuration panel state for PPT generation
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { 
  GenerateMarkdownRequest, 
  Tone, 
  Verbosity, 
  ExportFormat 
} from '../api/types/slidegen.types';
import { GENERATION_DEFAULTS } from '../utils/constants';
import { buildGenerationRequest } from './generationRequest';

type GenerationStep = 'configure' | 'generating' | 'editing';

interface GenerationState {
  // Workflow state
  currentStep: GenerationStep;
  markdownContent: string;
  selectedFiles: string[];
  generationParams: Partial<GenerateMarkdownRequest> | null;

  // Configuration panel state
  slideCount: number;
  language: string;
  template: string;
  tone: Tone;
  verbosity: Verbosity;
  exportFormat: ExportFormat;
  webSearchEnabled: boolean;
  uploadedFileIds: string[];

  // Actions - Workflow
  setStep: (step: GenerationStep) => void;
  setMarkdownContent: (content: string) => void;
  updateMarkdownContent: (content: string) => void;
  setSelectedFiles: (files: string[]) => void;
  setGenerationParams: (params: Partial<GenerateMarkdownRequest>) => void;
  reset: () => void;

  // Actions - Configuration
  setSlideCount: (count: number) => void;
  setLanguage: (language: string) => void;
  setTemplate: (template: string) => void;
  setTone: (tone: Tone) => void;
  setVerbosity: (verbosity: Verbosity) => void;
  setExportFormat: (format: ExportFormat) => void;
  setWebSearchEnabled: (enabled: boolean) => void;
  addUploadedFile: (fileId: string) => void;
  removeUploadedFile: (fileId: string) => void;
  clearUploadedFiles: () => void;

  // Computed
  getGenerationRequest: (
    content: string,
    userId: string,
    sessionId?: string,
    fileIds?: string[]
  ) => GenerateMarkdownRequest;
}

const initialState = {
  // Workflow
  currentStep: 'configure' as GenerationStep,
  markdownContent: '',
  selectedFiles: [],
  generationParams: null,
  
  // Configuration - use defaults
  slideCount: GENERATION_DEFAULTS.N_SLIDES,
  language: GENERATION_DEFAULTS.LANGUAGE,
  template: GENERATION_DEFAULTS.TEMPLATE,
  tone: GENERATION_DEFAULTS.TONE as Tone,
  verbosity: GENERATION_DEFAULTS.VERBOSITY as Verbosity,
  exportFormat: GENERATION_DEFAULTS.EXPORT_AS,
  webSearchEnabled: GENERATION_DEFAULTS.WEB_SEARCH,
  uploadedFileIds: [] as string[],
};

export const useGenerationStore = create<GenerationState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Workflow actions
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
        set({
          currentStep: 'configure',
          markdownContent: '',
          selectedFiles: [],
          generationParams: null,
          uploadedFileIds: [],
        });
      },

      // Configuration actions
      setSlideCount: (count: number) => {
        set({ slideCount: Math.max(1, Math.min(50, count)) });
      },

      setLanguage: (language: string) => {
        set({ language });
      },

      setTemplate: (template: string) => {
        set({ template });
      },

      setTone: (tone: Tone) => {
        set({ tone });
      },

      setVerbosity: (verbosity: Verbosity) => {
        set({ verbosity });
      },

      setExportFormat: (format: ExportFormat) => {
        set({ exportFormat: format });
      },

      setWebSearchEnabled: (enabled: boolean) => {
        set({ webSearchEnabled: enabled });
      },

      addUploadedFile: (fileId: string) => {
        set((state) => ({
          uploadedFileIds: [...state.uploadedFileIds, fileId],
        }));
      },

      removeUploadedFile: (fileId: string) => {
        set((state) => ({
          uploadedFileIds: state.uploadedFileIds.filter((id) => id !== fileId),
        }));
      },

      clearUploadedFiles: () => {
        set({ uploadedFileIds: [] });
      },

      // Build complete generation request from current config
      getGenerationRequest: (
        content: string,
        userId: string,
        sessionId?: string,
        fileIds?: string[]
      ) => {
        const state = get();
        return buildGenerationRequest(
          {
            tone: state.tone,
            verbosity: state.verbosity,
            webSearchEnabled: state.webSearchEnabled,
            slideCount: state.slideCount,
            language: state.language,
            template: state.template,
          },
          {
            content,
            userId,
            sessionId,
            fileIds: fileIds ?? state.uploadedFileIds,
          }
        );
      },
    }),
    {
      name: 'generation-config',
      // Only persist configuration, not workflow state
      partialize: (state) => ({
        slideCount: state.slideCount,
        language: state.language,
        template: state.template,
        tone: state.tone,
        verbosity: state.verbosity,
        exportFormat: state.exportFormat,
        webSearchEnabled: state.webSearchEnabled,
      }),
    }
  )
);
