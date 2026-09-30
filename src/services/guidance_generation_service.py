"""AgentCore Platform v1.0"""

# Service layer: domain queries, external API wrappers, data aggregation.
# Must NOT contain business logic, routing, or credentials.
# Nodes call this; this calls shared/services/ for external integrations.

from __future__ import annotations

from typing import Any

from src.services.mock_data import stub_guidance
from src.services.mock_mode import mock_mode_enabled


class GuidanceGenerationService:
    """LLM synthesis of zero-trust architecture guidance."""

    def generate(
        self,
        query: str,
        sub_domain: str,
        kb_chunks: list[dict[str, Any]],
        infra_context: dict[str, Any],
        credential_handle: str,
    ) -> str:
        """Synthesize a guidance recommendation from the query, KB chunks, and context.

        `credential_handle` is required by the real (non-mock) path — it is never
        used in mock mode, matching implementation_rule.md Rule 2 (mock mode must
        short-circuit before any credential is required).
        """
        if mock_mode_enabled():
            return stub_guidance(sub_domain, query)
        # Real LLM integration is out of scope for this iteration
        # (docs/implement_tasks.md Task 5) — fail fast rather than silently
        # returning a placeholder.
        raise NotImplementedError(
            "GuidanceGenerationService.generate: real (non-mock) LLM generation "
            "is not yet implemented for this template."
        )
