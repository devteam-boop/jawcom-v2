"""Template Renderer Service — replaces ``{{variable}}`` placeholders using a resolver.

Separates *template rendering* (``{{...}}`` pattern matching) from *variable
resolution* (dotted-path lookup). Future-ready for filter pipes::

    {{upper(lead.name)}}
    {{lower(company.name)}}
    {{date(today)}}
"""

import re
from typing import Any, Dict, Optional

from .variable_resolver_service import VariableResolverService


class TemplateRendererService:
    """Renders ``{{variable.path}}`` patterns by delegating path lookup to a
    ``VariableResolverService``.

    Usage::

        resolver = VariableResolverService(context)
        renderer = TemplateRendererService(resolver)
        renderer.render("Hello {{lead.name}}")  # → "Hello John"
    """

    PATTERN = re.compile(r"\{\{([\w.()]+)\}\}")

    def __init__(self, resolver: VariableResolverService):
        self._resolver = resolver

    # ── Public API ───────────────────────────────────────────────────

    def render(self, template: str) -> str:
        """Replace every ``{{variable}}`` in *template* with its resolved value.

        Unresolved placeholders (unknown path, missing key) are left as-is.
        """

        def _replace(match):
            inner = match.group(1)
            value = self._resolve_variable(inner)
            if value is None:
                return match.group(0)
            return str(value)

        return self.PATTERN.sub(_replace, template)

    def render_all(self, obj: Any) -> Any:
        """Recursively render variables in a nested structure.

        Handles ``str``, ``dict``, ``list``, and passthrough for other types.
        """
        if isinstance(obj, str):
            return self.render(obj)
        if isinstance(obj, dict):
            return {k: self.render_all(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.render_all(item) for item in obj]
        return obj

    def resolve_path(self, path: str) -> Optional[Any]:
        """Direct dotted-path lookup — delegates to the underlying resolver."""
        return self._resolver.resolve_path(path)

    # ── Internal helpers ─────────────────────────────────────────────

    def _resolve_variable(self, inner: str) -> Optional[Any]:
        """Resolve a single ``{{...}}`` inner expression.

        Currently supports plain dotted paths: ``lead.name``.
        Future: parse filter pipes like ``upper(lead.name)``.
        """
        return self._resolver.resolve_path(inner)
