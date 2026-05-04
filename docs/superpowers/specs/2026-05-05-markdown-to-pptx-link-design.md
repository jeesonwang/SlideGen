# Markdown-to-PPTX Frontend-Backend Link Fix

## Problem

The backend has a working `POST /api/v1/slidegen/generate-pptx-from-markdown` endpoint that accepts markdown content and returns a PPTX file. However, the frontend never calls it. The OutlineEditor's "Download" button only saves markdown locally as a `.md` file. The end-to-end link from editing markdown to downloading PPTX is broken.

## Changes

### 1. Fix `GeneratePPTXResponse` type

**File:** `web/src/api/types/slidegen.types.ts`

Replace the current type (which expects a non-existent `task_id`):

```typescript
// Before
interface GeneratePPTXResponse {
  message: string;
  task_id: string;
  download_url?: string;
}

// After
interface GeneratePPTXResponse {
  success: boolean;
  result: {
    output_path: string;
    filename: string;
    download_url: string;
  };
  message: string;
}
```

Also fix `downloadPPTX(taskId: string)` → `downloadPPTX(filename: string)` in `slidegen.ts`, since the parameter is a filename not a task ID.

### 2. Add `theme_preset` to `MarkdownToPPTRequest`

**File:** `web/src/api/types/slidegen.types.ts`

```typescript
export interface MarkdownToPPTRequest {
  markdown_content: string;
  template: string;
  export_as: ExportFormat;
  theme_preset?: string | null;  // added
}
```

### 3. Add backend endpoint for theme presets

**File:** `slidegen/api/routers/slidegen.py`

New endpoint: `GET /api/v1/slidegen/theme-presets`

Returns the list of available theme presets with their names and display labels:

```json
{
  "presets": [
    {"id": "ocean_depths", "name": "Ocean Depths"},
    {"id": "sunset_boulevard", "name": "Sunset Boulevard"},
    ...
  ]
}
```

### 4. Backend: forward `theme_preset` to generator

In both `generate-pptx-from-markdown` and `generate-pptx-from-markdown-stream`, pass `request.theme_preset` to the generator method call. Currently these parameters are accepted by the schema but dropped in the router handlers.

### 5. New ActionBubble component

**File:** `web/src/components/generation/ActionBubble.tsx` (new)

A compact bar displayed directly below the OutlineEditor, within the same assistant message bubble. Contains three elements in a horizontal row:

- **Template selector** — dropdown, populated from existing `/templates` endpoint
- **Theme selector** — dropdown, populated from new `/theme-presets` endpoint, with `null` = default theme
- **Generate PPTX button** — primary action button

States:
- **idle** — button shows "Generate PPTX"
- **generating** — button shows spinner + "Generating..."
- **done** — button shows "Download PPTX" (click triggers browser download via `result.download_url`)

Props:
```typescript
interface ActionBubbleProps {
  markdownContent: string;
  onGenerationStart?: () => void;
  onGenerationComplete?: (downloadUrl: string) => void;
  onError?: (error: string) => void;
}
```

The component manages its own `generating` and `downloadUrl` state internally. Template and theme selections default from `useGenerationStore`.

### 6. Wire ActionBubble into ChatInterface

**File:** `web/src/components/chat/ChatInterface.tsx`

In the rendering branch where `msg.role === 'assistant' && isOutlineMarkdown(msg.content)`, add `<ActionBubble>` directly below `<OutlineEditor>`, wrapping both in a container to keep them visually grouped within the same message bubble.

### 7. API client: add `getThemePresets` function

**File:** `web/src/api/endpoints/slidegen.ts`

```typescript
getThemePresets: async (): Promise<ThemePreset[]> => {
  const response = await apiClient.get<{ presets: ThemePreset[] }>(
    API_ENDPOINTS.SLIDEGEN.THEME_PRESETS
  );
  return response.data.presets;
}
```

Add `THEME_PRESETS: '/api/v1/slidegen/theme-presets'` to constants.

## What stays the same

- OutlineEditor component — no changes
- SSE markdown generation flow — no changes
- ChatInterface handleSend / handleGenerate — no changes
- Existing "Download" button in OutlineEditor — unchanged (still downloads .md)
- Existing "Refresh" button — unchanged

## Error handling

- Network errors during generation: show error message via antd `message.error`
- Backend returns `success: false`: display `result.error` in the UI
- Template/theme not found: backend returns 404, frontend shows error
