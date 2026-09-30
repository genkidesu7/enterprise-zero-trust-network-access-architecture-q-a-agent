# CMN-C1-721 — Unit Tests: Post-Process Node

import pytest
from framework.errors import SecurityViolationError
from framework.schemas.agent_status import AgentStatus

from src.nodes.post_process_node import PostProcessNode


class TestPostProcessNode:
    def setup_method(self):
        self.node = PostProcessNode()

    def test_appends_disclaimer(self):
        result = self.node.execute(
            {"result": "Use an identity-aware proxy.", "query_sub_domain": "identity_aware_proxy"}
        )
        assert result["status"] == AgentStatus.SUCCESS.value
        assert "Use an identity-aware proxy." in result["formatted_output"]
        assert "Advisory guidance only" in result["formatted_output"]

    def test_empty_result_still_succeeds(self):
        result = self.node.execute({"result": "", "query_sub_domain": "general"})
        assert result["status"] == AgentStatus.SUCCESS.value
        assert "Advisory guidance only" in result["formatted_output"]

    def test_extra_security_gate_output_rejects_ip_address(self):
        result = {"formatted_output": "Route traffic through 10.0.1.5/24."}
        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_output(result)

    def test_extra_security_gate_output_rejects_internal_hostname(self):
        result = {"formatted_output": "Point the proxy at gateway.internal."}
        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_output(result)

    def test_extra_security_gate_output_returns_result_on_clean_output(self):
        result = {"formatted_output": "Use an identity-aware proxy."}
        returned = self.node._extra_security_gate_output(result)
        assert returned is result
