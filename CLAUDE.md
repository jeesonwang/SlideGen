# CLAUDE.md

## Project Overview

SlideGen is an **AI agent-driven** slide generation service. It uses agents to plan, design, and compose presentations, producing PPTX/PDF from input. The backend is a FastAPI application; the frontend is a React SPA.

## Layered Architecture

The project follows a layered architecture with strict top-down call direction:

```
api/routers/          ← HTTP entry layer: parse requests, auth, validation, call services
    ↓
api/deps.py           ← Shared dependencies: DB sessions, current user, token parsing
    ↓
services/             ← Business logic layer: orchestrate workflows, query DB, generate output
    ↓
models/ + factories/  ← Data & factory layer: ORM models, LLM/Embedding factories
```

Supporting layers, called from anywhere within the call chain:

| Directory | Role |
|---|---|
| `schemas/` | Pydantic request/response schemas (distinct from ORM `models/`) |
| `core/` | Infrastructure: config, database, Redis, security, logging |
| `middleware/` | Cross-cutting: exception handling, rate limiting |

### Layer Responsibilities

| Layer | Directory | Allowed | Not Allowed |
|---|---|---|---|
| Router | `slidegen/api/routers/` | Parse HTTP requests, call `Depends` for current user, pass primitive values to services | No direct DB queries, no calling `get_llm_instance` or other data-access functions |
| Service | `slidegen/services/` | Orchestrate business flows, query database, create LLM instances, generate PPTX/PDF | No HTTP-level concerns (e.g., `Request` objects) |
| Factory | `slidegen/services/factories/` | Create LLM/Embedding instances from configs | No business logic |

### Core Rules

1. **Router layer passes only primitive values**: The router layer passes `user_id` (int), `template_name` (str), etc. to the service layer — never objects that require database queries to construct. Calls like `get_llm_instance` must happen inside services; the router layer should not be aware of them.

2. **Service method signatures stay clean**: `PresentationGenerator` `generate_*` methods accept `user_id: int | None` rather than LLM instances, and handle auto-theme LLM resolution internally.

3. **Lower-level methods retain injectability**: Methods like `_resolve_theme()` keep their `auto_theme_llm` parameter to support direct mock injection in tests.

## Web Frontend

The `web/` directory is a React 19 + TypeScript SPA:

| Technology | Usage |
|---|---|
| Vite 7 | Build tool & dev server |
| React 19 + React Router 7 | UI framework & routing |
| Ant Design 6 | Component library |
| TanStack Query 5 | Server state / data fetching |
| Zustand 5 | Client state management |
| React Hook Form 7 + Zod 4 | Form handling & validation |
| Tailwind CSS 3.4 | Utility-first styling |
| Axios | HTTP client |

Run `npm run dev` inside `web/` to start the frontend dev server.

## Testing

- Framework: pytest with `asyncio_mode=auto` (no need to decorate async tests with `@pytest.mark.asyncio`)
- **All async tests must be decorated with `@pytest.mark.anyio`** (the project uses anyio, not asyncio directly)
- Test files live in `test/` at the repo root, mirroring source modules (e.g., `test/test_config.py` for `slidegen/core/config.py`)
- Run tests: `uv run pytest` (or `uv run pytest test/test_config.py` for a single file)
- `pytest.ini` adds `-vv -s` by default and promotes warnings to errors (excluding `UserWarning` and `DeprecationWarning`)

## Key Files

- `slidegen/api/routers/slidegen.py` — Slide generation API endpoints
- `slidegen/api/deps.py` — FastAPI dependencies (`SessionDep`, `CurrentUser`, token parsing)
- `slidegen/services/presentation/generator.py` — `PresentationGenerator`, Markdown → PPTX/PDF
- `slidegen/services/slidegen/workflow.py` — Workflow orchestration, where `get_llm_instance` is defined
- `slidegen/schemas/gen_request.py` — Request schemas (`BaseGenerationRequest`, `GeneratePresentationRequest`)
- `slidegen/core/config.py` — Application settings via pydantic-settings
- `slidegen/core/database.py` — DB session factory (`get_db_session`, `get_sync_db_session`)

## Environment

- Use `uv` for Python dependency management; prefer `uv run` for running tests and scripts
- Test framework: pytest; async tests require `@pytest.mark.anyio`
