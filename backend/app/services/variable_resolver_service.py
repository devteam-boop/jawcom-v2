"""Variable Resolver Service — resolves {{variable.path}} patterns from runtime context."""

import re
from typing import Any, Dict, Optional
from datetime import datetime


class VariableResolutionError(Exception):
    """Raised when a variable cannot be resolved."""


class VariableResolverService:
    """Resolves ``{{variable.path}}`` patterns from a flat or nested context dict.

    Usage::

        ctx = {"lead": {"name": "John"}, "today": "2026-07-06"}
        resolver = VariableResolverService(ctx)
        resolver.resolve("Hello {{lead.name}}, today is {{today}}")
        # → "Hello John, today is 2026-07-06"
    """

    PATTERN = re.compile(r"\{\{([\w.]+)\}\}")

    def __init__(self, context: Dict[str, Any]):
        self._context = context

    def resolve(self, template: str) -> str:
        """Resolve all ``{{variable}}`` placeholders in *template*.

        Unresolved placeholders are left as-is.
        """

        def _replace(match):
            path = match.group(1)
            value = self._resolve_path(path)
            if value is None:
                return match.group(0)
            return str(value)

        return self.PATTERN.sub(_replace, template)

    def resolve_all(self, obj: Any) -> Any:
        """Recursively resolve variables in a nested structure.

        Handles ``str``, ``dict``, ``list``, and passthrough for other types.
        """
        if isinstance(obj, str):
            return self.resolve(obj)
        if isinstance(obj, dict):
            return {k: self.resolve_all(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.resolve_all(item) for item in obj]
        return obj

    def resolve_path(self, path: str) -> Optional[Any]:
        """Public alias for dotted-path lookup through the context dict.

        Example::

            resolver.resolve_path("lead.name")  # → "John"
        """
        return self._resolve_path(path)

    def _resolve_path(self, path: str) -> Optional[Any]:
        """Walk a dotted path through ``self._context``."""
        parts = path.split(".")
        current: Any = self._context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)) and part.isdigit():
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            elif hasattr(current, part):
                current = getattr(current, part, None)
            else:
                return None
            if current is None:
                return None
        return current
