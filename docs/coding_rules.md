# JAWCOM — Coding Rules

## Python Standards

### Style
- Python 3.10+ with async/await throughout
- Type hints required on all function signatures
- Follow PEP 8 (use `black` formatting)
- Docstrings on all public classes and methods (Google-style)
- Line length: 120 characters

### Async Patterns
- All database operations use async SQLAlchemy sessions
- All executors are `async def execute(...)` 
- Use `asyncio.sleep()` for simulated latency, never `time.sleep()`
- Database sessions via `async with self._session_factory() as session:`

### Imports
```python
# Standard library
import logging
from datetime import datetime
from typing import Any, Dict, Optional

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select

# Application
from app.services.journey_service import JourneyService
```

### File Structure (per module)
```
module/
    __init__.py      # exports
    schemas.py       # Pydantic models
    services.py      # Business logic
    validators.py    # Validation
    exceptions.py    # Custom exceptions
```

### Error Handling
```python
# Services raise ValueError for not-found, custom exceptions for business errors
try:
    journey = await journey_service.get(mapping.journey_id)
except ValueError:
    logger.warning("Journey %s not found, skipping", mapping.journey_id)
    continue
```

## React Standards

### Style
- Functional components with hooks (no class components)
- Use shadcn/ui primitives consistently
- Tailwind CSS for styling (no CSS modules)
- Import paths via `@/` alias

### Component Structure
```jsx
import { useState, useMemo, useEffect } from "react";
import Component from "@/components/Component";
import { Button } from "@/components/ui/button";

export default function MyComponent({ prop1, prop2 }) {
  const [state, setState] = useState(null);
  
  // Side effects in useEffect
  useEffect(() => { ... }, []);

  // Derived state in useMemo
  const computed = useMemo(() => ..., [deps]);
  
  // Event handlers
  const handleClick = () => { ... };
  
  return <div>...</div>;
}
```

### Data Fetching
- API calls through service wrappers in `src/services/`
- Use `useState` + `useEffect` for data fetching (no external state management)
- Auto-refresh via `setInterval` (10s polling, cleaned up in `useEffect` return)
- Loading state via boolean `loading` variable

## Patterns

### Factory Pattern (Backend)
```python
class Registry:
    _items: Dict[str, Type] = {}

    @classmethod
    def register(cls, name, klass):
        cls._items[name] = klass

    @classmethod
    def get(cls, name):
        klass = cls._items.get(name)
        if not klass:
            raise ValueError(f"Unknown: {name}")
        return klass()
```

### Service Layer (Backend)
```python
class SomeService:
    def __init__(self, session):
        self._repo = SomeRepository(session)
    
    async def get(self, id):
        return await self._repo.get(id)
    
    async def create(self, schema):
        return await self._repo.create(schema.dict())
```

### Executor Pattern (Backend)
```python
class SomeExecutor(BaseNodeExecutor):
    @property
    def node_type(self) -> str:
        return "some_type"

    async def execute(self, node, running_instance, lead_id, context, exec_ctx=None):
        started_at = datetime.utcnow()
        node_config = node.get("config") or {}
        # ... read config, resolve variables, execute, log ...
        return ExecutionResult(success=True, ...)
```

## Naming Conventions

| Layer | Convention | Example |
|---|---|---|
| Routes | `{entity}_routes.py` | `journey_routes.py` |
| Services | `{entity}_service.py` | `journey_service.py` |
| Repositories | `{entity}_repository.py` | `journey_repository.py` |
| Models | PascalCase | `RunningJourneyInstance` |
| Executors | `{type}_executor.py` | `send_whatsapp_executor.py` |
| Schemas | `{Entity}Schema` | `RunningInstanceSchema` |
| Frontend services | camelCase | `runningInstanceService` |
| Frontend components | PascalCase | `JourneyMonitor` |

## Logging

```python
logger = logging.getLogger(__name__)
logger.info("Human-readable message with key=%s values=%s", key, value)
```

- Use structured logging with `%s` placeholders (never f-strings in log messages)
- Levels: `DEBUG` for development, `INFO` for normal operations, `WARNING` for recoverable issues, `ERROR` for failures

## Testing
- No formal test framework yet (to be added)
- Manual QA via the Test Execution endpoint + Execution Monitor
- Future: pytest for backend, React Testing Library for frontend

## Validation
- `FlowValidationService` handles all flow validation
- Validation is called by the Publish endpoint before changing status
- Validation errors return HTTP 400 with structured error list
- Never validate inside executors (separation of concerns)
