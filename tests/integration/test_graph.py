# CMN-C1-721 — Integration Test: full .compile() + .invoke() path
#
# A unit test that calls execute()/route() directly with a stubbed dict
# bypasses LangGraph's schema projection entirely and can pass while the
# compiled graph is actually broken. This test drives the real compiled
# graph end to end.

from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel
from framework.secrets.context import bound_secrets
from shared.secrets.inmemory_provider import InMemoryProvider

from src.graph.graph import ZeroTrustQAGraph


def _build_agent() -> ZeroTrustQAGraph:
    agent = ZeroTrustQAGraph(config={"max_retry": 1})
    agent.compile()
    agent.provision_secrets(InMemoryProvider({}))
    return agent


def test_invoke_success_path_in_mock_mode(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")
    agent = _build_agent()
    ctx = InvocationContext(caller_trust_level=TrustLevel.VERIFIED_EXTERNAL)

    with bound_secrets(InMemoryProvider({})):
        result = agent.invoke(
            "How should we design an identity-aware proxy to replace VPN access?",
            ctx=ctx,
        )

    assert result["status"] == "success"
    assert result["output"]
    assert result["node_history"] == [
        "InitializeNode",
        "PreProcessNode",
        "MainNode",
        "PostProcessNode",
        "FinalizeNode",
    ]


def test_invoke_s1_denied_when_caller_trust_insufficient(monkeypatch):
    """MainNode requires VERIFIED_EXTERNAL; a default ANONYMOUS caller is denied."""
    monkeypatch.setenv("USE_MOCK", "true")
    agent = _build_agent()
    ctx = InvocationContext(caller_trust_level=TrustLevel.ANONYMOUS)

    with bound_secrets(InMemoryProvider({})):
        result = agent.invoke("How should we design an identity-aware proxy?", ctx=ctx)

    assert result["status"] == "error"


def test_invoke_s2_gate_blocks_internal_ip_in_input(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")
    agent = _build_agent()
    ctx = InvocationContext(caller_trust_level=TrustLevel.VERIFIED_EXTERNAL)

    with bound_secrets(InMemoryProvider({})):
        result = agent.invoke("How do I configure 10.0.1.5/24 for zero trust?", ctx=ctx)

    assert result["status"] == "error"
