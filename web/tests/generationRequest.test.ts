import assert from 'node:assert/strict';
import { Tone, Verbosity } from '../src/api/types/slidegen.types.ts';
import { buildGenerationRequest } from '../src/store/generationRequest.ts';

const request = buildGenerationRequest(
  {
    tone: Tone.DEFAULT,
    verbosity: Verbosity.STANDARD,
    webSearchEnabled: false,
    slideCount: 8,
    language: 'English',
    template: 'general',
  },
  {
    content: 'Generate a project status review',
    userId: 'user-1',
    sessionId: 'session-1',
    fileIds: ['file-a', 'file-b'],
  }
);

assert.deepEqual(request.files, ['file-a', 'file-b']);

console.log('generationRequest.test.ts passed');
