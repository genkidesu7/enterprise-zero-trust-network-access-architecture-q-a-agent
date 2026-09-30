# CMN-C1-721 — Integration Test: HTTP-level /invoke over a real ASGI transport
#
# test_rule.md Rule 3: src/api/server.py's /invoke route is async and wraps a
# sync agent.invoke() (whose nodes internally use asyncio.run()). Calling
# agent.invoke() directly from a synchronous test function never enters an
# event loop and cannot reproduce "asyncio.run() cannot be called from a
# running event loop". Only a test that drives the ASGI app itself, on a real
# event loop, exercises that boundary.

import importlib

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_invoke_endpoint_succeeds_over_http(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("INVOKE_AUTH_TOKEN", "test-invoke-token")

    # Import (and its module-level agent.compile()) must happen after
    # USE_MOCK/INVOKE_AUTH_TOKEN are set, and fresh per test run to avoid
    # cross-test agent reuse.
    import src.api.server as server_module

    importlib.reload(server_module)

    transport = ASGITransport(app=server_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/invoke",
            json={"input": "How should we design an identity-aware proxy to replace VPN access?"},
            headers={"authorization": "Bearer test-invoke-token"},
        )

    assert resp.status_code == 200
    body = resp.json()
    # The standalone dev server has no auth middleware, so caller_trust_level
    # defaults to ANONYMOUS unless the caller presents INVOKE_AUTH_TOKEN as a
    # Bearer token (server.py's entry-point auth boundary), which elevates it
    # to VERIFIED_EXTERNAL — required by MainNode. A "success" status here
    # proves the async-route/sync-invoke boundary is fixed: if agent.invoke()
    # were still called synchronously from this async route,
    # asyncio.run() inside the node would raise "cannot be called from a
    # running event loop", which the node's except-Exception silently turns
    # into status: "error" with a 200 response — this would fail the
    # assertion below instead of raising visibly.
    assert body["status"] == "success"
    assert body["output"]


@pytest.mark.asyncio
async def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")
    import src.api.server as server_module

    importlib.reload(server_module)

    transport = ASGITransport(app=server_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
