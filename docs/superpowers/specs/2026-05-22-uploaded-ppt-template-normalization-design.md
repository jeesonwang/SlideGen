# Uploaded PPT Template Normalization Design

## Goal

Allow users to upload an ordinary PPTX file, have the backend detect reusable slide roles, convert suitable slides into a structured template profile, and let future generation requests reuse that uploaded PPT as a template.

The upload flow must not assume users have prepared legacy placeholder-based templates. A PPTX can be a finished presentation. The backend should extract role and slot semantics from it, preserve enough style information for reuse, and mark uncertain results for review instead of rejecting the file outright.

## Non-Goals

- This design does not implement a frontend review editor.
- This design does not require every uploaded PPTX to become a fully ready template.
- This design does not remove the existing legacy placeholder renderers.
- This design does not make LLM output authoritative without deterministic validation.

## Core Idea

Template preparation is split into four independent stages:

1. Extract deterministic slide features and thumbnails from the uploaded PPTX.
2. Ask an LLM to classify slide roles and suggest reusable slots.
3. Validate the LLM output and build a `TemplateProfile`.
4. Normalize each selected role slide into a renderable template source.

Role detection and render compatibility are separate concerns. A slide can be semantically identified as `cover` while still being unsupported by the legacy placeholder renderer. In that case it can enter slot normalization instead of being treated as missing.

## Service Boundaries

The router layer should only accept the upload request, resolve `current_user.id`, and call the upload service with primitive values. PPT parsing, LLM lookup, role classification, persistence, and template normalization belong in services.

Proposed service boundaries:

- `user_templates.py`: owns upload orchestration, storage, database persistence, listing, deletion, and generation-time resolution.
- `template_profile.py`: owns deterministic slide feature extraction, profile dataclasses, validation, and fallback heuristic scoring.
- `template_classifier.py`: owns LLM prompt construction, model invocation, and JSON parsing.
- `template_normalizer.py`: owns conversion from a selected source slide to reusable slot metadata.
- `converter.py`: consumes the persisted profile and chooses `legacy`, `normalized`, or native fallback rendering per role.

This keeps the upload workflow consistent with the existing layered architecture and keeps LLM creation out of API routers.

## Upload Flow

1. The user uploads a PPTX.
2. The upload service validates ownership, extension, size, and readability.
3. The backend extracts slide features with `python-pptx`.
4. The thumbnail service generates one image per slide or a reusable grid preview.
5. The LLM classifier receives structured slide features plus optional thumbnail references.
6. The classifier returns role assignments, confidence, reasons, and suggested slots.
7. The backend validates the response and creates a persisted profile.
8. The normalizer processes each assigned role slide:
   - Placeholder-compatible slides use the existing legacy renderer.
   - Plain-text slides are converted into slot descriptors such as `title`, `subtitle`, `body`, `footer`, `list`, and `card`.
   - Unclear slides are saved as `review_required`.
9. The uploaded template remains selectable. Generation later decides per role whether to use legacy rendering, normalized-slot rendering, or native fallback.

## Slide Features

Feature extraction should stay deterministic and testable. Each slide feature record should include:

- `slide_index`
- extracted text lines
- text shape count and total shape count
- placeholder counts by type
- title-like text candidates
- body-like text candidates
- numbered/list-like text patterns
- text box geometry, font size, font weight, color, alignment, and approximate bounding box
- image, table, chart, and grouped-shape counts
- background color or dominant theme hints when cheaply available
- thumbnail path or identifier when generated

The existing `SlideFeatures` can be extended instead of replaced, but it should not stay limited to text and placeholder counts.

## LLM Classifier

The classifier should receive a compact JSON payload, not raw PPTX bytes. It should classify only the slides in the uploaded deck and return strict JSON.

Expected output shape:

```json
{
  "assignments": [
    {
      "role": "cover",
      "slide_index": 0,
      "semantic_confidence": 0.86,
      "reason": "First slide has a large main title, subtitle, and report metadata.",
      "suggested_slots": [
        {
          "slot": "title",
          "source_shape_id": "shape-12",
          "confidence": 0.91
        }
      ]
    }
  ],
  "missing_roles": ["chapter"],
  "ambiguous_roles": []
}
```

The prompt should define each role narrowly:

- `cover`: opening page for the whole deck.
- `catalog`: agenda, table of contents, or presentation structure page.
- `chapter`: section divider page with little body content.
- `content`: reusable body/content layout page.
- `end`: closing, thanks, Q&A, or contact page.

The model should be allowed to mark a role missing. It should not be forced to assign all roles when the PPTX does not contain them.

## Validation

The backend validates LLM output before persisting it.

Validation rules:

- role values must be known `TemplateRole` values.
- slide indexes must exist.
- each role can have at most one selected slide in the final profile.
- duplicate slide assignments are allowed only if explicitly configured; default is one role per slide.
- confidence must be numeric and normalized to `0.0` through `1.0`.
- low-confidence assignments remain persisted but drive `review_required`.
- malformed JSON falls back to deterministic heuristic profiling.
- suspicious or contradictory output is ignored with a warning.

The validator should preserve the existing maximum-weight assignment idea: score or rank candidates per role, then choose the best non-conflicting role-to-slide assignment.

## Template Profile Contract

`TemplateProfile` should distinguish role semantics from renderer support.

Each assignment should include:

- `role`
- `slide_index`
- `semantic_confidence`
- `reason`
- `renderer_mode`: `legacy`, `normalized`, or `native_fallback`
- `renderer_supported`
- `normalization_status`: `ready`, `review_required`, or `failed`
- `slots`

Profile-level fields should include:

- `slide_count`
- `assignments`
- `missing_roles`
- `unsupported_roles`
- `review_required_roles`
- `warnings`
- `status`

`status` should mean the template is ready for automated reuse, not merely that roles were semantically detected. A profile with good semantic detection can still be `review_required` if normalizer confidence is too low.

## Normalizer

The normalizer converts ordinary PPT slides into reusable slot metadata.

For a placeholder-compatible slide:

- keep `renderer_mode = legacy`;
- keep using the existing `CoverPage`, `CatalogPage`, `ChapterHomePage`, `ChapterContentPage`, and `EndPage` renderers.

For a plain PPT slide:

- infer slots from text geometry, font size, visual grouping, and LLM slot suggestions;
- store the original slide as the style source;
- store slot descriptors that identify which shapes can be replaced during generation;
- set `renderer_mode = normalized` only when required slots are present with enough confidence.

Slot examples:

- `title`
- `subtitle`
- `body`
- `footer`
- `list`
- `card`
- `catalog_item`
- `chapter_number`

If required slots are missing or ambiguous, set `normalization_status = review_required` and let generation use native fallback for that role until a review workflow exists.

## Generation Flow

When a user selects an uploaded template:

1. Resolve the uploaded template through the database-backed template service.
2. Load the persisted `TemplateProfile`.
3. For each role needed by the render plan:
   - use `legacy` when the selected slide supports the existing placeholder renderer;
   - use `normalized` when slot metadata is ready;
   - use native fallback when the role is missing, unsupported, or review-required.
4. Log the selected renderer mode per role.
5. Keep cleanup based on stable `slide_id`, not transient indexes.

This preserves current fallback behavior while letting uploaded ordinary PPTX files improve over time as normalization gets stronger.

## Error Handling

- Empty or unreadable PPTX files fail upload.
- LLM failures do not fail upload if deterministic profiling can produce a reviewable profile.
- Invalid LLM JSON is logged and ignored.
- Normalizer failures mark only the affected role as `review_required`.
- Generation should not crash because a role was detected semantically but lacks a compatible renderer.

## Testing

Add focused tests for:

- plain PPTX with no placeholders still receives semantic role assignments;
- semantic assignment does not imply `ready` when renderer support is missing;
- LLM classifier JSON is validated and malformed output falls back cleanly;
- duplicate/conflicting role assignments are resolved deterministically;
- normalizer marks role slides `ready` only when required slots are present;
- generation falls back per role when normalized metadata is missing or review-required;
- existing curated placeholder templates still use legacy renderers.

## Rollout

Phase 1 extends profile contracts and separates semantic detection from renderer support.

Phase 2 adds the LLM classifier behind a service boundary and keeps heuristic fallback.

Phase 3 adds slot normalization for common plain-text layouts: cover, content, and end first; catalog and chapter can follow.

Phase 4 adds optional user review and manual role/slot correction.

## Decisions

- Run the first implementation synchronously during upload, with a timeout and deterministic fallback. A background task can be added later if classification latency becomes a product issue.
- Start with structured slide features as the required LLM input. Store thumbnails and include thumbnail references in the contract, but do not require multimodal classification in the first pass.
- Start normalization with `cover`, `content`, and `end`; these have simpler slot requirements and give the most immediate value for ordinary PPTX uploads.
- Default to one role per slide. Multi-role reuse can be introduced later as an explicit advanced behavior for small decks.
