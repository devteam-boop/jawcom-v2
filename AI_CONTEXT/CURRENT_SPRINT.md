# Current Sprint Context

> Lightweight engineering context. Last updated: 2026-07-02.

## Current Architecture

```
backend/app/
├── main.py              # FastAPI entry, GET /health
├── pipeline.py          # Event processing chain
├── config/              # Settings + logging
├── core/                # BaseRepository, BaseService, deps
├── database/            # SQLAlchemy async engine + session
├── models/              # 11 SQLAlchemy domain models
├── providers/           # Provider abstraction (WhatsApp/Email)
│   ├── base/            # Abstract provider interfaces
│   ├── registry/        # ProviderRegistry (DI container)
│   └── meta/            # Meta WhatsApp (placeholder)
├── communication/       # CommunicationEngine (message orchestration)
├── events/              # Event system (BaseEvent, Dispatcher, Handlers)
├── jawis/               # JAWIS API client + webhook handler
├── journeys/            # Journey Engine (service + manager)
├── flows/               # Flow Definition Engine (service + builder)
├── templates/           # Template Engine (service + renderer)
├── stage_mapping/       # Stage Mapping Engine (service + manager)
├── runtime/             # Running Instance Engine (service + manager)
└── workers/             # Empty (future Celery tasks)
```

Database: PostgreSQL via SQLAlchemy 2.0 Async + asyncpg (11 tables).

## Completed Sprints

| Sprint | Module | Status |
|---|---|---|
| Sprint 1 | Backend Foundation (config, database, core) | Done |
| Sprint 2 | Provider Registry (WhatsApp/Email abstraction) | Done |
| Sprint 3 | Communication Engine | Done |
| Sprint 4 | Event System + JAWIS Integration | Done |
| Sprint 5 | Business Domain Models + 5 Engines (Journeys, Flows, Templates, Stage Mapping, Runtime) | Done |

## Current Backend Status

- **75 modules created** across config, core, database, providers, communication, events, jawis, journeys, flows, templates, stage_mapping, runtime, models, pipeline
- **Backend product APIs**: 0 routes (only `GET /health`)
- **Service layer**: All CRUD services written but not exposed via HTTP
- **Event system**: Fully scaffolded with dispatcher, handlers, and retry
- **JAWIS integration**: API client with caching, webhook handler with batch processing
- **Model layer**: 11 SQLAlchemy tables with relationships and enums
- **Issues**: Merge conflict in `server.py`, missing `resend_provider.py`, legacy MongoDB `.env`, duplicate `Base` classes

## Current Frontend Status

- 16+ static pages with dummy data
- 46 shadcn/Radix UI primitives
- Flow Builder with visual canvas
- Service layer placeholders (not wired to backend)
- Frontend modules: inbox, journeys, campaigns, templates, reports

## Current Milestone

Resolve build/setup issues blocking backend API development:
- Fix `server.py` merge conflict
- Create missing `resend_provider.py`
- Migrate `.env` to PostgreSQL config
- Clean up `.gitignore` merge conflict

## Pending Milestones

1. Backend product API routes for all 5 business engines
2. Flow Execution Engine (graph walker for Running Instances)
3. Real WhatsApp/Email channel integration
4. Campaign execution engine
5. Auth (JWT) + RBAC
6. Workers/Celery for async tasks

## Known Technical Debt

1. `server.py` — merge conflict between old MongoDB scaffold and new `app.main`
2. `providers/__init__.py` — imports non-existent `ResendProvider`
3. `.env` — still has legacy MongoDB config; needs `DATABASE_URL` for PostgreSQL
4. `.gitignore` — has merge conflict markers
5. `communication/engine.py` — uses local `WhatsAppProvider` instead of providers module
6. `database/base.py` vs `models/base.py` — two separate `declarative_base()` declarations
7. No API routes exist despite complete service layer
8. No tests written for any backend module
9. `requirements.txt` missing `httpx`, `jinja2` (used in code but not listed)

## Next Development Task

Resolve the merge conflict in `backend/server.py` to enable clean startup via `python -m backend.server`.
