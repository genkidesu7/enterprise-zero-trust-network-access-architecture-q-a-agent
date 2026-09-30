"""AgentCore Platform v1.0"""

import re
from typing import Any, ClassVar

from framework.errors import SecurityViolationError
from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

_DISCLAIMER = (
    "\n\n---\nAdvisory guidance only, generated from public NIST/BeyondCorp/ZTNA "
    "vendor documentation. Not a substitute for a formal security review before "
    "any production access-control change."
)

# S-3 domain check: block internal network topology from ever leaving the
# pipeline (docs/01_proposal.md §4), in addition to the framework's default
# credential-pattern scan.
_IPV4_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?\b")
_INTERNAL_HOSTNAME_RE = re.compile(r"\b[\w-]+\.(?:internal|corp|local|lan)\b", re.IGNORECASE)


class PostProcessNode(FunctionNode):
    """Format and finalize the output; attach the advisory disclaimer."""

    # S-1: explicit by design, not inherited implicitly.
    # Matches the agent-level required trust level (VERIFIED_EXTERNAL).
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """S-3 domain extension: reject IP/CIDR/internal-hostname leakage.

        Runs after the default credential-pattern scan. Must return result —
        see creat-node skill Common Mistakes (returning None silently becomes
        the node output).
        """
        output = result.get("formatted_output", "")
        if isinstance(output, str):
            if _IPV4_RE.search(output) or _INTERNAL_HOSTNAME_RE.search(output):
                raise SecurityViolationError(
                    "PostProcessNode S-3: internal network topology detected " "in formatted_output — blocked"
                )
        return result

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        result = state.get("result", "") or ""

        formatted_output = f"{result}{_DISCLAIMER}"

        emit_trace_event(
            "output_validated",
            {"sub_domain": state.get("query_sub_domain", "general")},
            state,
        )

        return {
            "formatted_output": formatted_output,
            "status": AgentStatus.SUCCESS.value,
        }
