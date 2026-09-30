# CMN-C1-721 — Unit Tests: KB Retrieval + Guidance Generation Services

import pytest

from src.services.guidance_generation_service import GuidanceGenerationService
from src.services.kb_retrieval_service import KBRetrievalService


class TestKBRetrievalService:
    def test_mock_mode_returns_fixture_chunks(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        service = KBRetrievalService()
        chunks = service.retrieve("device_trust", "device posture check")
        assert chunks
        assert all("content" in c and "source" in c for c in chunks)

    def test_mock_mode_unknown_sub_domain_falls_back_to_general(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        service = KBRetrievalService()
        chunks = service.retrieve("not_a_real_sub_domain", "anything")
        assert chunks

    def test_real_mode_raises_not_implemented(self, monkeypatch):
        monkeypatch.delenv("USE_MOCK", raising=False)
        monkeypatch.delenv("STG_MOCK_MODE", raising=False)
        service = KBRetrievalService()
        with pytest.raises(NotImplementedError):
            service.retrieve("policy_design", "access control policy")


class TestGuidanceGenerationService:
    def test_mock_mode_succeeds_without_credential_handle(self, monkeypatch):
        """Mock mode must never require a real credential_handle."""
        monkeypatch.setenv("USE_MOCK", "true")
        service = GuidanceGenerationService()
        guidance = service.generate(
            query="migration sequencing plan",
            sub_domain="migration_sequencing",
            kb_chunks=[{"content": "x", "source": "y", "score": 0.5}],
            infra_context={},
            credential_handle="",
        )
        assert guidance

    def test_real_mode_raises_not_implemented(self, monkeypatch):
        monkeypatch.delenv("USE_MOCK", raising=False)
        monkeypatch.delenv("STG_MOCK_MODE", raising=False)
        service = GuidanceGenerationService()
        with pytest.raises(NotImplementedError):
            service.generate(
                query="q",
                sub_domain="general",
                kb_chunks=[],
                infra_context={},
                credential_handle="real-handle",
            )
