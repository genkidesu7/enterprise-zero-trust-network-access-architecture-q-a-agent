"""AgentCore Platform v1.0"""

# Service layer: domain queries, external API wrappers, data aggregation.
# Must NOT contain business logic, routing, or credentials.
# Nodes call this; this calls shared/services/ for external integrations.

from __future__ import annotations

from typing import Any

from src.services.mock_data import stub_kb_chunks
from src.services.mock_mode import mock_mode_enabled


class KBRetrievalService:
    """Cosine-similarity retrieval over the zero-trust architecture KB."""

    def retrieve(self, sub_domain: str, query: str) -> list[dict[str, Any]]:
        """Retrieve KB chunks relevant to `query`, scoped by `sub_domain`."""
        if mock_mode_enabled():
            return stub_kb_chunks(sub_domain)
        # Real vector-DB integration is out of scope for this iteration
        # (docs/implement_tasks.md Task 4) — fail fast rather than silently
        # returning an empty/placeholder result.
        raise NotImplementedError(
            "KBRetrievalService.retrieve: real (non-mock) KB retrieval is not " "yet implemented for this template."
        )
