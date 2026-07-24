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

    # Well-known nested namespaces this context always carries (see
    # ExecutionContext.to_dict()) — used only as a fallback lookup for a
    # bare, dot-less variable name that doesn't match a top-level context
    # key, e.g. a template author writing {{first_name}} instead of the
    # fully-qualified {{lead.first_name}}. Existing dotted paths are
    # completely unaffected by this list.
    _BARE_NAME_FALLBACK_NAMESPACES = ("lead", "company")

    def _resolve_path(self, path: str) -> Optional[Any]:
        """Walk a dotted path through ``self._context``.

        A bare (dot-less) name that comes up empty at the top level is then
        looked up inside the well-known nested namespaces above — e.g.
        ``{{first_name}}`` resolves against ``lead.first_name`` without the
        template needing the "lead." prefix. This only ever fires when the
        direct top-level lookup for a single-segment path found nothing;
        every existing dotted path (``{{lead.first_name}}``,
        ``{{company.name}}``, ``{{today}}``, ...) resolves exactly as before.

        A bare name that happens to collide with a reserved top-level
        namespace key itself (``{{company}}``, ``{{lead}}``) is also routed
        through this fallback rather than returned as the raw namespace
        dict: a template author writing ``{{company}}`` means the flat
        ``lead.company``/``company.company`` scalar field (the same as every
        other bare-name variable in the standard contract), never the
        internal context object. If no nested namespace has a same-named
        scalar field either, the original (dict) value is returned
        unchanged — existing behavior for any bare name with no scalar
        equivalent is preserved.
        """
        parts = path.split(".")
        current: Any = self._context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)) and part.isdigit():
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    current = None
                    break
            elif hasattr(current, part):
                current = getattr(current, part, None)
            else:
                current = None
                break
            if current is None:
                break

        direct_hit_is_reserved_namespace = (
            len(parts) == 1
            and path in self._BARE_NAME_FALLBACK_NAMESPACES
            and isinstance(current, dict)
        )

        if (
            (current is None or direct_hit_is_reserved_namespace)
            and len(parts) == 1
            and isinstance(self._context, dict)
        ):
            for namespace in self._BARE_NAME_FALLBACK_NAMESPACES:
                namespace_value = self._context.get(namespace)
                if isinstance(namespace_value, dict):
                    fallback_value = namespace_value.get(path)
                    if fallback_value is not None:
                        return fallback_value

        return current
