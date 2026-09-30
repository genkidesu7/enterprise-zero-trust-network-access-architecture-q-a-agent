"""AgentCore Platform v1.0"""

# Single shared mock-mode resolver — every service must import this instead of
# re-deriving its own env check. `deploy-stg` sets STG_MOCK_MODE (CI-script-only
# variable); local/unit tests set USE_MOCK. Both must be honored (see
# .claude/rules/implementation_rule.md Rule 1).

import os

_TRUE_VALUES = {"true", "1", "yes"}


def mock_mode_enabled() -> bool:
    """Return True if mock mode is on via USE_MOCK or STG_MOCK_MODE (either alias)."""
    use_mock = os.environ.get("USE_MOCK", "").strip().lower()
    stg_mock_mode = os.environ.get("STG_MOCK_MODE", "").strip().lower()
    return use_mock in _TRUE_VALUES or stg_mock_mode in _TRUE_VALUES
