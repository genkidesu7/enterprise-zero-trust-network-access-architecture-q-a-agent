"""AgentCore Platform v1.0"""

# Node contract (agents_layer_design.md §1):
#  - Extend FunctionNode; implement execute(state) -> dict
#  - Return ONLY the fields this node changes (never full state)
#  - Return AgentStatus enum constants — never plain strings [A1]
#  - Read input_context via state.get("input_context", {}) — read-only [C1]
#  - Never import from mediator/, api/, or other agents

import re
from typing import Any, ClassVar

from framework.errors import SecurityViolationError
from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

# Sub-domain classification keywords (docs/02_design.md Architecture Overview).
# Checked in order; first match wins. Unmatched input falls back to "general".
_SUB_DOMAIN_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("identity_aware_proxy", ("identity-aware proxy", "identity aware proxy", "iap", "beyondcorp")),
    ("microsegmentation", ("microsegmentation", "micro-segmentation", "segment", "lateral movement")),
    ("device_trust", ("device trust", "device posture", "endpoint posture", "device compliance")),
    ("policy_design", ("policy", "policy engine", "access control", "authorization model")),
    ("migration_sequencing", ("migration", "migrate", "rollout", "phase", "cutover")),
]

# S-2 domain check: reject raw internal-network-topology tokens before they
# reach the LLM prompt — the proposal requires that no internal topology or
# credential data ever enters the pipeline (docs/01_proposal.md §4).
_IPV4_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?\b")
_INTERNAL_HOSTNAME_RE = re.compile(r"\b[\w-]+\.(?:internal|corp|local|lan)\b", re.IGNORECASE)


def _classify_sub_domain(text: str) -> str:
    lowered = text.lower()
    for sub_domain, keywords in _SUB_DOMAIN_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return sub_domain
    return "general"


class PreProcessNode(FunctionNode):
    """Validate incoming input and classify its ZTNA sub-domain."""

    # S-1: explicit by design, not inherited implicitly.
    # Matches the agent-level required trust level (VERIFIED_EXTERNAL).
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_input(self, state: dict[str, Any]) -> dict[str, Any]:
        """S-2 domain extension: reject raw IP/CIDR/internal-hostname tokens.

        Runs after the default PII scan. Must return state — see creat-node
        skill Common Mistakes (returning None crashes the framework).
        """
        user_input = state.get("user_input", "")
        if isinstance(user_input, str):
            if _IPV4_RE.search(user_input):
                raise SecurityViolationError("PreProcessNode S-2: raw IP/CIDR address detected in user_input")
            if _INTERNAL_HOSTNAME_RE.search(user_input):
                raise SecurityViolationError("PreProcessNode S-2: internal hostname detected in user_input")
        return state

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        user_input = state.get("user_input", "")
        input_context = state.get("input_context", {})  # read-only [C1]

        if not user_input or not user_input.strip():
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": ["PreProcessNode: user_input is empty or missing"],
            }

        validated_input = user_input.strip()
        sub_domain = _classify_sub_domain(validated_input)

        emit_trace_event(
            "query_classified",
            {"sub_domain": sub_domain},
            state,
        )

        return {
            "validated_input": validated_input,
            "query_sub_domain": sub_domain,
            "enriched_context": {
                "source": "zero_trust_qa_agent",
                "channel": input_context.get("channel", "unknown"),
            },
            "status": AgentStatus.SUCCESS.value,
        }
