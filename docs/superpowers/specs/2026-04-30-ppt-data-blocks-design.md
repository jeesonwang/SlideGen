# PPT Data Blocks Design

Date: 2026-04-30
Status: approved for planning

## Context

SlideGen currently generates Markdown first, parses it with `MarkdownDocument`, and converts it into PowerPoint through `MarkdownToPresentation` and page generators under `slidegen/services/presentation/`. The current content-slide path is optimized for text, icons, pictures, and template-driven point layouts. Markdown tables are parsed as `Table` elements, but they are not rendered as PowerPoint tables, and there is no chart/data visualization contract.

The goal is to support tables and business reporting charts in generated PPTX files while keeping the first implementation scoped and deployable.

## Confirmed Decisions

- Scope will be phased. The long-term goal includes both user-authored data blocks and LLM-authored data blocks, but the first phase keeps editing as raw Markdown.
- Markdown will use HTML-style extension tags, so future frontend code can recognize and render the same blocks without changing the authoring format.
- The frontend will not add a dedicated table/chart editor in the first phase. Users edit the original Markdown text.
- Tables should be rendered as native PowerPoint tables where possible.
- Charts should be rendered to images and inserted into PPTX. Native editable PowerPoint charts are deferred because `python-pptx` chart generation and combo chart behavior would add unnecessary first-phase complexity.
- Default data mode is real-data-only. Simulated/example data is allowed only when the user explicitly asks for it.
- First-phase chart families are table, bar, line, area, stacked bar, and combo charts.

## Goals

- Parse explicit table and chart blocks from Markdown.
- Convert valid table blocks into PowerPoint-native tables.
- Convert valid chart blocks into server-rendered chart images and insert them into slides.
- Preserve existing text-only generation behavior when no data blocks are present.
- Give clear, user-facing errors for invalid data-block syntax and validation failures.
- Keep the internal block model compatible with a future structured frontend editor.

## Non-Goals

- Build a visual table/chart editor in the first phase.
- Generate native editable PowerPoint chart objects in the first phase.
- Add advanced chart types such as scatter, radar, funnel, gauge, or dashboards.
- Let the model invent numeric data by default.
- Redesign the entire template system.

## Markdown Contract

Data blocks use HTML-style tags inside Markdown. The tag body is JSON. JSON is chosen for strict validation, easy frontend parsing, and predictable LLM output.

### Table

```markdown
<data-table title="季度收入">
{
  "columns": ["季度", "收入", "成本"],
  "rows": [
    ["Q1", 120, 80],
    ["Q2", 150, 95],
    ["Q3", 180, 110]
  ],
  "unit": "万元",
  "source": "uploaded-file",
  "note": "来自用户上传的经营数据",
  "allow_simulated_data": false
}
</data-table>
```

### Chart

```markdown
<data-chart type="bar" title="季度收入趋势">
{
  "x": ["Q1", "Q2", "Q3"],
  "series": [
    {"name": "收入", "data": [120, 150, 180]},
    {"name": "成本", "data": [80, 95, 110]}
  ],
  "unit": "万元",
  "source": "uploaded-file",
  "note": "展示收入与成本变化",
  "allow_simulated_data": false
}
</data-chart>
```

### Combo Chart

```markdown
<data-chart type="combo" title="收入与利润率">
{
  "x": ["Q1", "Q2", "Q3"],
  "series": [
    {"name": "收入", "data": [120, 150, 180], "chart_type": "bar"},
    {"name": "利润率", "data": [0.18, 0.21, 0.24], "chart_type": "line", "axis": "secondary"}
  ],
  "source": "uploaded-file",
  "allow_simulated_data": false
}
</data-chart>
```

## Data Model

Introduce an internal block model between Markdown parsing and PPT rendering:

- `TextBlock`: existing headings and paragraph content.
- `TableBlock`: title, columns, rows, unit, source, note, and simulated-data flag.
- `ChartBlock`: type, title, x categories, series, unit, source, note, simulated-data flag, and optional per-series chart options.

This model is a backend boundary first. It should not force the frontend to stop editing Markdown, but it should be serializable so a future editor can render and edit the same blocks visually.

## Parsing Strategy

Add a data-block parser that runs before or alongside the existing Markdown parser:

1. Detect `<data-table>` and `<data-chart>` tag ranges.
2. Parse tag attributes such as `title` and `type`.
3. Parse the tag body as JSON.
4. Replace or attach the parsed block in the Markdown tree so `ChapterContentPage` can see it.
5. Preserve surrounding text and headings exactly as they work today.

The parser should reject malformed data blocks early with line-oriented errors. It should not silently treat broken data blocks as plain text, because that would produce misleading PPT output.

## Generation Flow

### User-Edited Markdown Path

`/generate-pptx-from-markdown` receives Markdown, parses data blocks, validates them, and generates PPTX.

### LLM Markdown Path

The outline and content prompts may allow data blocks, but with strict constraints:

- The model may create a data block only when numeric/tabular data is present in uploaded references or explicitly provided by the user.
- If the user explicitly asks for simulated/example data, the model may set `allow_simulated_data: true`.
- If data is unavailable, the model should write text instead of inventing a chart.
- The model must output valid JSON inside data tags.

## Rendering Strategy

### Tables

Use `slide.shapes.add_table()` to generate native PowerPoint tables.

Rules:

- Validate that every row has the same length as `columns`.
- Use a compact table style with readable header emphasis.
- Fit small and medium tables on the current slide.
- Split large tables across slides when they exceed configured row limits.
- Add source or note text under the table when provided.

### Charts

Use a server-side static chart renderer, with Matplotlib as the first implementation choice. It keeps the dependency surface Python-native and avoids browser or Node runtime requirements during PPT generation.

Rules:

- Render charts to temporary PNG files.
- Insert chart images with `slide.shapes.add_picture()`.
- Support `bar`, `line`, `area`, `stacked_bar`, and `combo`.
- For combo charts, render mixed bar/line series in one image and support an optional secondary axis.
- Add source or note text under the chart when provided.
- Clean up temporary chart images after successful PPT generation or task failure.

## Slide Layout Strategy

Keep existing template-based generation for text-only slides. When a chapter contains `TableBlock` or `ChartBlock`, switch that content slide to a data-aware layout.

Initial data layouts:

1. Single data block: slide title on top, table/chart in the main body, note/source at the bottom.
2. Text plus chart/table: concise text summary on the left, data block on the right.
3. Table plus chart: chart above and compact table below, or split into multiple slides if either block exceeds size limits.

The first implementation can use code-defined geometry based on slide dimensions. Template-specific data placeholders can be introduced later.

## Validation And Errors

Validation happens after parsing and before rendering.

Hard errors:

- Invalid JSON inside a data tag.
- Missing required fields.
- Unsupported chart type.
- Table row length does not match columns.
- Chart series length does not match `x`.
- Non-numeric chart values where numeric values are required.
- `allow_simulated_data: true` without an explicit user instruction allowing simulated data.

Soft failures:

- A chart rendering exception should not crash the whole PPT conversion. Insert a visible placeholder explaining that chart rendering failed, and emit a warning in logs and stream events.
- Oversized tables should split across slides when possible. If splitting is not possible, render the first rows and include a truncation note.
- Too many chart series should still render, but with smaller labels and a warning.

## Streaming And API Behavior

The existing Markdown-to-PPT endpoints stay stable.

SSE generation should add progress/warning events for:

- data block parsing
- table rendering
- chart image rendering
- fallback placeholder insertion

Existing clients that ignore unknown event details should continue to work.

## Testing Plan

Backend tests:

- Parse valid `<data-table>` and `<data-chart>` blocks.
- Reject malformed JSON with a clear error.
- Reject table rows with inconsistent column counts.
- Reject chart series whose data length does not match `x`.
- Reject unsupported chart types.
- Verify text-only Markdown still follows the existing path.
- Verify a table block creates a PowerPoint table shape.
- Verify a chart block creates a picture shape.
- Verify chart renderer failure inserts a placeholder and does not fail the whole PPT generation.
- Verify simulated data is rejected unless explicitly allowed by the request/instructions.

Frontend/source tests:

- Ensure Markdown editor does not strip data tags.
- Ensure generated Markdown can be submitted unchanged to PPT conversion.
- Keep visible UI copy English-only in the current frontend.

Manual validation:

- Generate a PPTX containing one table, one bar chart, one line chart, one stacked bar chart, and one combo chart.
- Open or inspect the PPTX to confirm tables are native table shapes and charts are picture shapes.
- Confirm source/note text appears near the corresponding data block.

## Implementation Phases

### Phase 1: Explicit Blocks

- Add block data models and validators.
- Add parser support for `<data-table>` and `<data-chart>`.
- Render native PowerPoint tables.
- Render chart images with Matplotlib and insert them into PPTX.
- Add focused backend tests and one end-to-end PPTX generation test.

### Phase 2: LLM-Aware Blocks

- Update generation prompts to allow data tags under the real-data rules.
- Add tests for prompt constraints and simulated-data gating.
- Add SSE warnings for data-block validation and rendering fallbacks.

### Phase 3: Future Frontend Upgrade

- Parse data tags in the frontend for preview.
- Add optional visual editors for table/chart blocks.
- Reuse the same block schema instead of inventing a separate frontend model.

## Acceptance Criteria

- Existing text-only PPT generation remains unchanged.
- A Markdown table block produces a PPTX with a native table.
- A Markdown chart block produces a PPTX with an inserted chart image.
- Supported chart types include bar, line, area, stacked bar, and combo.
- Invalid data blocks fail with actionable messages.
- Chart rendering failure degrades to a visible placeholder instead of crashing generation.
- LLM-generated charts cannot use simulated data unless the user explicitly permits simulated/example data.
