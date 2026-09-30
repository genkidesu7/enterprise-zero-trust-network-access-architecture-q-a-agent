"""AgentCore Platform v1.0"""

# Deterministic fixture data for mock mode. No network, no credentials.

from __future__ import annotations

from typing import Any

_KB_FIXTURES: dict[str, list[dict[str, Any]]] = {
    "identity_aware_proxy": [
        {
            "content": "An identity-aware proxy (IAP) authenticates and authorizes every "
            "request at the application layer, replacing perimeter VPN trust with "
            "per-request identity and device posture checks.",
            "source": "NIST SP 800-207 §4.2",
            "score": 0.92,
        },
        {
            "content": "BeyondCorp Enterprise routes all traffic through a proxy that "
            "enforces context-aware access policies before granting access to internal "
            "applications.",
            "source": "BeyondCorp Research",
            "score": 0.88,
        },
    ],
    "microsegmentation": [
        {
            "content": "Microsegmentation partitions the network into granular zones so "
            "that a compromised workload cannot move laterally beyond its own segment.",
            "source": "NIST SP 800-207 §5.1",
            "score": 0.91,
        },
    ],
    "device_trust": [
        {
            "content": "Device trust evaluates posture signals (patch level, disk "
            "encryption, endpoint agent health) as a precondition for access, independent "
            "of network location.",
            "source": "NIST SP 800-207 §3.3",
            "score": 0.90,
        },
    ],
    "policy_design": [
        {
            "content": "Zero-trust policy engines evaluate subject, resource, and "
            "environmental attributes on every access decision rather than granting "
            "standing network-level trust.",
            "source": "NIST SP 800-207 §3.1",
            "score": 0.89,
        },
    ],
    "migration_sequencing": [
        {
            "content": "A phased ZTNA migration typically starts with a pilot application "
            "group, expands to identity-aware proxy coverage, then retires legacy VPN "
            "access paths last.",
            "source": "BeyondCorp Research",
            "score": 0.87,
        },
    ],
    "general": [
        {
            "content": "Zero-trust architecture assumes no implicit trust based on network "
            "location and instead verifies every access request explicitly.",
            "source": "NIST SP 800-207 §1",
            "score": 0.80,
        },
    ],
}


def stub_kb_chunks(sub_domain: str) -> list[dict[str, Any]]:
    """Deterministic mock KB retrieval result for the given sub-domain."""
    return _KB_FIXTURES.get(sub_domain, _KB_FIXTURES["general"])


def stub_guidance(sub_domain: str, query: str) -> str:
    """Deterministic mock guidance-generation result."""
    return (
        f"[mock guidance for sub-domain='{sub_domain}'] Based on NIST SP 800-207 and "
        f"BeyondCorp guidance, recommended approach for: {query.strip()!r}"
    )
