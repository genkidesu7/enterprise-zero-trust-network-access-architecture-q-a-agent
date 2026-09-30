# CMN-C1-721 — Unit Tests: Pre-Process Node

import pytest
from framework.errors import SecurityViolationError
from framework.schemas.agent_status import AgentStatus

from src.nodes.pre_process_node import PreProcessNode


class TestPreProcessNode:
    def setup_method(self):
        self.node = PreProcessNode()

    def test_empty_input_returns_error(self):
        result = self.node.execute({"user_input": "", "input_context": {}})
        assert result["status"] == AgentStatus.ERROR.value
        assert result["error_log"]

    @pytest.mark.parametrize(
        "text,expected_sub_domain",
        [
            ("What's the best identity-aware proxy pattern?", "identity_aware_proxy"),
            ("How do I set up microsegmentation for lateral movement?", "microsegmentation"),
            ("What device posture checks should I require?", "device_trust"),
            ("How should the policy engine evaluate access control?", "policy_design"),
            ("What's a safe migration rollout sequence?", "migration_sequencing"),
            ("Tell me about zero trust in general", "general"),
        ],
    )
    def test_classification(self, text, expected_sub_domain):
        result = self.node.execute({"user_input": text, "input_context": {}})
        assert result["status"] == AgentStatus.SUCCESS.value
        assert result["query_sub_domain"] == expected_sub_domain
        assert result["validated_input"] == text

    def test_extra_security_gate_input_rejects_ip_address(self):
        state = {"user_input": "How do I configure 10.0.1.5/24 for zero trust?"}
        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_input(state)

    def test_extra_security_gate_input_rejects_internal_hostname(self):
        state = {"user_input": "Can host db01.internal reach the proxy?"}
        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_input(state)

    def test_extra_security_gate_input_returns_state_on_clean_input(self):
        state = {"user_input": "How should I design an identity-aware proxy?"}
        result = self.node._extra_security_gate_input(state)
        assert result is state
