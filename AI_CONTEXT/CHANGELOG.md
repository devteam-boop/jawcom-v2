# Changelog

## Sprint 1
### Backend Foundation

**Completed:**
- Application settings via Pydantic `BaseSettings` (`.env` support, CORS, logging config)
- Logging configuration with JSON or text format
- SQLAlchemy async PostgreSQL engine and session factory
- Base model (`DeclarativeBase`) for all domain models
- Generic `BaseRepository` with CRUD operations
- Abstract `BaseService` with CRUD interface
- FastAPI DB session dependency
- FastAPI application factory with `GET /health` endpoint
- `server.py` entry point with uvicorn

**Files:**
- `backend/app/config/__init__.py`
- `backend/app/config/settings.py`
- `backend/app/config/logging.py`
- `backend/app/database/base.py`
- `backend/app/database/database.py`
- `backend/app/database/session.py`
- `backend/app/core/base_repository.py`
- `backend/app/core/base_service.py`
- `backend/app/core/dependencies.py`
- `backend/app/core/__init__.py`
- `backend/app/main.py`
- `backend/server.py`
- `backend/requirements.txt`

---

## Sprint 2
### Provider Registry

**Completed:**
- Abstract `CommunicationProvider` base class (send_message, get_message_status, validate_recipient)
- Abstract `WhatsAppProvider` with template message, media upload, template status methods
- Abstract `EmailProvider` with email send, template email, bounce status methods
- `MessageStatus` and `MessageType` enums
- `MetaProvider` — Meta WhatsApp Business API implementation (placeholder with mock responses)
- `ProviderRegistry` — dependency injection container for channel-based provider lookup
- Global `provider_registry` singleton

**Files:**
- `backend/app/providers/__init__.py`
- `backend/app/providers/base/communication_provider.py`
- `backend/app/providers/base/whatsapp_provider.py`
- `backend/app/providers/base/email_provider.py`
- `backend/app/providers/registry/provider_registry.py`
- `backend/app/providers/meta/meta_provider.py`

**Notes:**
- `ResendProvider` is imported in `providers/__init__.py` but the file does not exist
- Provider implementations are placeholders — no real API calls

---

## Sprint 3
### Communication Engine

**Completed:**
- `CommunicationEngine` — orchestrator for sending messages via template service + provider
- Mock `WhatsAppProvider` (local to communication module, separate from providers module)
- Template rendering pipeline (template lookup → render → send via provider)

**Files:**
- `backend/app/communication/__init__.py`
- `backend/app/communication/engine.py`
- `backend/app/communication/providers.py`

**Notes:**
- Communication engine uses its own `WhatsAppProvider` instead of the providers module's abstraction
- Only WhatsApp channel implemented; Email channel not wired

---

## Sprint 4
### Event System & JAWIS Integration

**Completed:**
- `BaseEvent` — abstract base with event_id, timestamp, source, priority, retry logic
- `EventHandler` — abstract handler interface
- `EventDispatcher` — central dispatcher with handler registration, async dispatch, queuing, retry
- 4 typed JAWIS events: `LeadCreatedEvent`, `LeadStageChangedEvent`, `LeadAssignedEvent`, `LeadRequirementMetEvent`
- `CommunicationEventHandler` — handles business events and logs trigger actions
- `LoggingEventHandler` — logs all events for auditing
- `MetricsEventHandler` — collects event processing statistics
- `JawisClient` — read-only API client with in-memory caching (5-min TTL)
- `JawisWebhookHandler` — webhook receiver that converts webhook payloads to internal events
- Pydantic schemas for JAWIS data: `LeadSchema`, `CompanySchema`, `StageSchema`, `UserSchema`, `LeadContextSchema`
- Global singletons: `get_dispatcher()`, `get_jawis_client()`, `get_webhook_handler()`

**Files:**
- `backend/app/events/__init__.py`
- `backend/app/events/base_event.py`
- `backend/app/events/event_types.py`
- `backend/app/events/dispatcher.py`
- `backend/app/events/handlers.py`
- `backend/app/jawis/__init__.py`
- `backend/app/jawis/client.py`
- `backend/app/jawis/webhook.py`
- `backend/app/jawis/schemas.py`
- `backend/app/pipeline.py`

---

## Sprint 5
### Business Domain Modules

**Completed:**
- 11 SQLAlchemy domain models with UUID PKs, timestamps, relationships, and enums
- `Journey Engine` — CRUD service, state management (draft/active/paused/archived), trigger-based lookup, validation
- `Flow Definition Engine` — CRUD service, publish/version management, `FlowBuilder` helper, comprehensive validation (circular references, orphan nodes, template references)
- `Template Engine` — CRUD service, Jinja2-based rendering with `StrictUndefined`, variable extraction, email/WhatsApp validation
- `Stage Mapping Engine` — CRUD service, trigger-based lookup, business hours/retry policy configuration, duplicate prevention
- `Running Instance Engine` — CRUD service, state management (pause/resume/cancel/complete), duplicate instance prevention
- Pipeline module for processing JAWIS events through the communication chain

**Domain Models:**
| Table | Key Fields |
|---|---|
| `workspaces` | name, slug, is_active |
| `users` | email, first_name, last_name, role (admin/member/viewer) |
| `journeys` | name, status, workspace_id, flow_definition_id |
| `templates` | name, subject, content, channel, status, workspace_id |
| `flow_definitions` | definition (JSON blob), journey_id |
| `stage_mappings` | name, journey_id, template_id |
| `running_journey_instances` | status, started_at, journey_id, conversation_id |
| `conversations` | channel, recipient_id, workspace_id |
| `messages` | content, direction, status, sent_at, conversation_id |
| `campaigns` | name, status, scheduled_at, workspace_id, template_id |
| `campaign_recipients` | recipient_id, status, sent_at, campaign_id |

**Files:**
- `backend/app/models/base.py`
- `backend/app/models/workspace.py`
- `backend/app/models/user.py`
- `backend/app/models/journey.py`
- `backend/app/models/template.py`
- `backend/app/models/flow_definition.py`
- `backend/app/models/stage_mapping.py`
- `backend/app/models/running_journey_instance.py`
- `backend/app/models/conversation.py`
- `backend/app/models/message.py`
- `backend/app/models/campaign.py`
- `backend/app/models/campaign_recipient.py`
- `backend/app/models/__init__.py`
- `backend/app/journeys/services.py`
- `backend/app/journeys/schemas.py`
- `backend/app/journeys/validators.py`
- `backend/app/journeys/journey_manager.py`
- `backend/app/journeys/exceptions.py`
- `backend/app/journeys/__init__.py`
- `backend/app/flows/services.py`
- `backend/app/flows/schemas.py`
- `backend/app/flows/validators.py`
- `backend/app/flows/flow_builder.py`
- `backend/app/flows/exceptions.py`
- `backend/app/flows/__init__.py`
- `backend/app/templates/services.py`
- `backend/app/templates/schemas.py`
- `backend/app/templates/validators.py`
- `backend/app/templates/renderer.py`
- `backend/app/templates/exceptions.py`
- `backend/app/templates/__init__.py`
- `backend/app/stage_mapping/services.py`
- `backend/app/stage_mapping/schemas.py`
- `backend/app/stage_mapping/validators.py`
- `backend/app/stage_mapping/mapping_manager.py`
- `backend/app/stage_mapping/exceptions.py`
- `backend/app/stage_mapping/__init__.py`
- `backend/app/runtime/services.py`
- `backend/app/runtime/schemas.py`
- `backend/app/runtime/validators.py`
- `backend/app/runtime/instance_manager.py`
- `backend/app/runtime/exceptions.py`
- `backend/app/runtime/__init__.py`
- `backend/app/pipeline.py`

---

## Known Issues (as of 2026-07-02)

1. `backend/server.py` has an unresolved merge conflict between old MongoDB scaffold and new `app.main`
2. `backend/app/providers/__init__.py` imports `ResendProvider` but `backend/app/providers/resend/resend_provider.py` is missing
3. `backend/.env` still contains legacy MongoDB config (`MONGO_URL`, `DB_NAME`) instead of PostgreSQL `DATABASE_URL`
4. `.gitignore` has merge conflict markers
5. `backend/app/communication/engine.py` uses its own local `WhatsAppProvider` instead of the providers module's abstraction
6. `backend/app/models/base.py` (database layer) and `backend/app/models/base.py` (model layer) — two separate `Base` classes with the same name
7. `backend/app/database/base.py` uses `declarative_base()` while `backend/app/models/base.py` uses `BaseModel + declarative_base()` — potential duplication
