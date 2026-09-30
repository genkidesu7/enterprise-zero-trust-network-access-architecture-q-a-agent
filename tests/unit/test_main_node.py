# CMN-C1-721 — Unit Tests: Main Node

import inspect

from framework.schemas.agent_status import AgentStatus

from src.nodes.main_node import MainNode


class TestMainNode:
    """Unit tests for the main business logic node."""

    def setup_method(self):
        self.node = MainNode()

    def test_success_path(self, monkeypatch):
        """TC: Main node processes valid input and returns SUCCESS in mock mode."""
        monkeypatch.setenv("USE_MOCK", "true")
        monkeypatch.delenv("STG_MOCK_MODE", raising=False)
        state = {
            "validated_input": "How should we design an identity-aware proxy?",
            "query_sub_domain": "identity_aware_proxy",
            "input_context": {},
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert result["result"]
        assert result["kb_chunks"]

    def test_empty_input(self, monkeypatch):
        """TC: Main node returns ERROR when validated_input is missing."""
        monkeypatch.setenv("USE_MOCK", "true")
        state = {
            "validated_input": "",
            "query_sub_domain": "general",
            "input_context": {},
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.ERROR.value

    def test_mock_mode_succeeds_with_no_secret_provider_bound(self, monkeypatch):
        """Regression test (test_rule.md Rule 2): a fresh CI checkout has no
        env/ secret tree at all. Mock mode must not depend on a secret being
        resolvable — run this WITHOUT any bound_secrets() context."""
        monkeypatch.setenv("USE_MOCK", "true")
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        state = {
            "validated_input": "microsegmentation strategy for lateral movement",
            "query_sub_domain": "microsegmentation",
            "input_context": {},
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value

    def test_execute_method_signature(self):
        """Node must implement execute(state) not _invoke_impl.

        Canonical contract:
          - Override: execute(self, state: AgentState) -> dict
          - PROHIBITED: _invoke_impl(), process() override
        """
        assert hasattr(MainNode, "execute"), "MainNode must implement execute()"

        sig = inspect.signature(MainNode.execute)
        params = list(sig.parameters.keys())
        assert len(params) >= 2, f"execute() must accept (self, state), got params: {params}"
        assert params[1] == "state", f"Second parameter must be 'state', got '{params[1]}'"

        assert (
            "_invoke_impl" not in MainNode.__dict__
        ), "_invoke_impl() must not be defined in MainNode — use execute() instead"
