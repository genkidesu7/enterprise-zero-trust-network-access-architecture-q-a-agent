"""AgentCore Platform v1.0"""

from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.guidance_generation_service import GuidanceGenerationService
from src.services.kb_retrieval_service import KBRetrievalService
from src.services.mock_mode import mock_mode_enabled


class MainNode(FunctionNode):
    """Retrieve KB context and synthesize zero-trust architecture guidance."""

    # S-1: explicit by design. VERIFIED_EXTERNAL — this node
    # resolves an LLM credential handle (implementation_rule.md §2/§3).
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        kb_service = KBRetrievalService()
        guidance_service = GuidanceGenerationService()

        validated_input = state.get("validated_input", state.get("user_input", ""))
        sub_domain = state.get("query_sub_domain", "general")
        input_context: dict[str, Any] = state.get("input_context", {})

        if not validated_input:
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": ["MainNode: validated_input missing"],
            }

        infra_context = {
            "existing_infrastructure": input_context.get("existing_infrastructure", ""),
            "compliance_requirements": input_context.get("compliance_requirements", []),
            "team_maturity": input_context.get("team_maturity", "unknown"),
        }

        # Mock mode must short-circuit before any credential is required
        # (implementation_rule.md Rule 2) — mock services never touch
        # credential_handle.
        credential_handle = (
            "mock"
            if mock_mode_enabled()
            else InvocationContext.from_state(state).secrets.require("AZURE_OPENAI_API_KEY")
        )

        try:
            kb_chunks = kb_service.retrieve(sub_domain, validated_input)
        except NotImplementedError as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": [f"MainNode: KB retrieval unavailable — {exc}"],
            }

        if not kb_chunks:
            return {
                "status": AgentStatus.RETRY.value,
                "error_log": ["MainNode: no KB chunks retrieved, retrying classification"],
            }

        emit_trace_event(
            "kb_retrieved",
            {"sub_domain": sub_domain, "chunk_count": len(kb_chunks)},
            state,
        )

        try:
            guidance_draft = guidance_service.generate(
                query=validated_input,
                sub_domain=sub_domain,
                kb_chunks=kb_chunks,
                infra_context=infra_context,
                credential_handle=credential_handle,
            )
        except NotImplementedError as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": [f"MainNode: guidance generation unavailable — {exc}"],
            }

        emit_trace_event(
            "guidance_generated",
            {"sub_domain": sub_domain, "chars": len(guidance_draft)},
            state,
        )

        return {
            "kb_chunks": kb_chunks,
            "infra_context": infra_context,
            "guidance_draft": guidance_draft,
            "result": guidance_draft,
            "status": AgentStatus.SUCCESS.value,
        }
