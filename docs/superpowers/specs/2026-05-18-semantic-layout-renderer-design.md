# Semantic Layout Renderer Design

Date: 2026-05-18
Status: proposed for review

## Context

SlideGen currently converts generated or user-edited Markdown into PowerPoint through `MarkdownDocument`, `MarkdownToPresentation`, and page generators under `slidegen/services/presentation/`.

The current content-slide path is driven by `components/shapes/shapes.json`. `ChapterContentPage` counts the direct children under a chapter heading, maps that count to `one_point`, `two_points`, `three_points`, or `four_points`, randomly selects a style, copies stored PowerPoint XML, and replaces placeholder text or images.

This keeps extracted PowerPoint styles visually close to the source template, but it makes layout decisions depend on static shape samples rather than content semantics. It is hard to support long text, tables, charts, comparison pages, process pages, timelines, data-heavy slides, or predictable design choices.

## Goals

- Replace count-driven slide layout with semantic slide and block models.
- Keep existing Markdown-first authoring and `/generate-pptx-from-markdown` API behavior stable.
- Preserve the current template and `shapes.json` path for compatible text-only slides during migration.
- Add a deterministic layout-selection layer that can choose layouts based on content type, density, and assets.
- Render common slide structures with `python-pptx` native APIs instead of raw XML copying where possible.
- Keep `shapes.json` useful as an optional decorative/style asset library, not the primary layout engine.
- Create clear boundaries for future table, chart, and frontend visual editing support.

## Non-Goals

- Redesign the entire frontend editor in the first phase.
- Remove existing templates or delete `shapes.json` immediately.
- Require LLM output to switch to a large structured JSON format in one step.
- Build native editable PowerPoint charts in the first phase.
- Guarantee pixel-perfect equivalence with every existing extracted shape style.

## Proposed Architecture

The new generation path introduces three explicit layers:

```text
MarkdownDocument
  -> SlideSpec / BlockSpec
  -> LayoutSelector
  -> LayoutRecipe
  -> Renderer
  -> PPTX
```

### SlideSpec And BlockSpec

`SlideSpec` is the semantic representation of one generated slide. It describes what the slide is trying to communicate, not how it is drawn.

Initial slide kinds:

- `cover`
- `agenda`
- `section_cover`
- `content_points`
- `comparison`
- `process`
- `timeline`
- `image_text`
- `data_table`
- `data_chart`
- `mixed_data`
- `closing`

`BlockSpec` describes the content units inside a slide.

Initial block kinds:

- `title`
- `subtitle`
- `paragraph`
- `bullet_list`
- `numbered_list`
- `image`
- `icon`
- `table`
- `chart`
- `note`
- `source`

The first implementation can derive these specs from the existing Markdown tree. Later, the LLM prompt can emit more explicit Markdown extension tags for tables, charts, comparisons, and timelines.

### LayoutSelector

`LayoutSelector` receives a `SlideSpec` and chooses a `LayoutRecipe`.

Selection inputs:

- slide kind
- block kinds
- number of blocks
- estimated text length
- whether the slide has image/table/chart assets
- template or theme metadata
- fallback compatibility mode

This replaces the current `len(content)` to `ChapterLayout` mapping. The selector should be deterministic by default. Random selection can remain as an opt-in style variation after a suitable layout family is chosen.

### LayoutRecipe

`LayoutRecipe` describes regions, typography, spacing, and rendering rules. It should be code-defined at first so it can adapt to slide dimensions and content density.

Examples:

- `TitleBodyRecipe`: title region plus one body region.
- `TwoColumnRecipe`: left/right content regions with balanced widths.
- `ComparisonRecipe`: two to four comparable panels.
- `ProcessRecipe`: horizontal or vertical steps.
- `TimelineRecipe`: ordered milestones.
- `DataFullBleedRecipe`: title plus table/chart occupying the main body.
- `ChartWithNotesRecipe`: chart region plus concise insight and source regions.

Each recipe should expose enough metadata for testing, such as expected regions and supported block kinds.

### Renderer

The renderer converts a chosen recipe into PowerPoint shapes.

Preferred rendering order:

1. Use `python-pptx` native APIs for text boxes, tables, pictures, and basic shapes.
2. Use theme colors and typography from the template where possible.
3. Use copied XML from `shapes.json` only for decorative accents or legacy-compatible text styles.

This keeps generated PPTX files easier to reason about and makes table/chart support less fragile.

## Migration Strategy

### Phase 1: Add Semantic Model Beside Existing Renderer

Introduce `SlideSpec`, `BlockSpec`, and a Markdown-to-spec adapter. Keep current PPT output behavior unchanged by default.

Expected result:

- Existing generation still passes.
- Unit tests can inspect semantic specs without generating PPTX.
- Chapters with one to three point headings map to `content_points` specs.

### Phase 2: Add Deterministic LayoutSelector

Add layout selection for common content types while still allowing a legacy fallback to `ChapterContentPage`.

Expected result:

- Text-only slides can continue through existing `shapes.json` styles.
- Data/table/chart/comparison/process slides can select new recipes.
- Random style selection no longer decides the slide structure.

### Phase 3: Add Native Renderers For New Layout Families

Implement native renderers for the highest-value recipes first:

- title/body
- two-column
- comparison
- process
- data table
- data chart image

Expected result:

- Slides with data or strong structure no longer depend on static extracted shapes.
- Long text and varied block counts can be handled with recipe-specific overflow rules.

### Phase 4: Gradually Move Text Slides Off Raw XML

After new renderers are stable, migrate existing text-only content pages from raw XML copying to native recipe rendering. Keep `shapes.json` for template accents and compatibility where useful.

Expected result:

- `shapes.json` becomes optional style metadata.
- Adding a new slide type no longer requires extracting PowerPoint XML from a sample deck.

## Data And Chart Alignment

This design should compose with the existing approved data-block direction:

- Markdown remains the authoring surface.
- Tables should become native PowerPoint table shapes.
- Charts should initially be rendered to images and inserted into slides.
- Data-aware slides should use semantic layouts rather than count-driven point layouts.

The semantic model should therefore include table and chart blocks early, even if chart rendering lands after basic text recipes.

## Compatibility Rules

- Existing API routes should not change in the first phase.
- Existing templates should continue to load through `PresentationGenerator`.
- Existing generated Markdown without special tags should still produce PPTX files.
- Legacy renderer fallback should be explicit and testable.
- User-provided theme presets should continue to apply before rendering.

## Risks

- A semantic model that is too broad could become another hard-to-maintain abstraction. Keep the first block and slide kinds small.
- Native rendering may initially look less decorative than copied PowerPoint XML. Use template theme colors and selective decorative accents to recover visual polish.
- LLM output may not reliably express richer slide semantics at first. Derive basic semantics from Markdown structure before expanding prompt contracts.
- Layout recipes need overflow handling from the start, or they will recreate the current fixed-coordinate limitations.

## Testing Plan

Backend tests:

- Parse simple Markdown into `SlideSpec` and `BlockSpec`.
- Verify one chapter with child headings maps to `content_points`.
- Verify Markdown tables map to table blocks.
- Verify future data tags map to data block specs.
- Verify `LayoutSelector` chooses deterministic recipes for text, comparison, and data slides.
- Verify unsupported semantic combinations fall back to the legacy renderer.
- Verify existing Markdown-to-PPT generation still succeeds during phase 1.

PPTX inspection tests:

- Verify native-rendered text recipes create expected text shapes.
- Verify native-rendered tables create PowerPoint table shapes.
- Verify chart-image recipes create picture shapes.
- Verify legacy fallback can still use `shapes.json`.

## Recommended First Implementation Scope

The first implementation should stop before replacing the current renderer. It should add only:

1. Semantic model classes.
2. Markdown-to-spec adapter.
3. Deterministic layout selector skeleton.
4. Tests proving current Markdown can be represented semantically.
5. A feature flag or explicit code path that keeps current PPT output unchanged.

This creates a safe foundation for renderer replacement without changing user-visible generation behavior in the same step.
