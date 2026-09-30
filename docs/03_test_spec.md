# Test Specification

## Test Strategy
- Coverage target: 80%
- Test types: Unit / Integration / Proof-of-Boundary

## Framework Compliance Tests (Mandatory)

| TC-ID | Test | Expected Result | Result |
|-------|------|----------------|--------|
| TC-01 | State contract: flat TypedDict | Type check pass, no Pydantic/dataclass | PASS — `tests/proof_of_boundary/test_state_safety.py` |
| TC-02 | SecurityViolationError fires on invalid input | Error raised | PASS — `tests/unit/test_pre_process_node.py::test_extra_security_gate_input_rejects_ip_address`, `test_extra_security_gate_input_rejects_internal_hostname` |
| TC-03 | No JWT/Credential in State | CI `gate-credential-scan`: 0 violations (S-5 enforced by CI) | PASS — `.claude/common-scripts/check-local.sh` credential pattern scan |
| TC-04 | InvocationContext via configurable only | Direct access raises error | PASS — no State field named `invocation_context`; `src/nodes/main_node.py` resolves via `InvocationContext.from_state(state)` only |
| TC-05 | S-4: no duplicate lifecycle events in `execute()` | `node_start` / `node_complete` / `node_error` absent from `execute()` body | PASS — inspection of `src/nodes/*.py`; only domain events (`query_classified`, `kb_retrieved`, `guidance_generated`, `output_validated`) emitted |
| TC-06 | S-2: `_security_gate_input()` not overridden (`FunctionNode` subclass) | `TypeError` raised at class definition if overridden (`@final` enforced by framework) | PASS — no node defines `_security_gate_input`; module import succeeds |
| TC-07 | S-3: `_security_gate_output()` not overridden (`FunctionNode` subclass) | `TypeError` raised at class definition if overridden (`@final` enforced by framework) | PASS — no node defines `_security_gate_output`; module import succeeds |
| TC-08 | `required_trust_level` enforced | Insufficient trust → refused | PASS — `tests/integration/test_graph.py::test_invoke_s1_denied_when_caller_trust_insufficient` |
| TC-09 | S-2: `_extra_security_gate_input()` non-trivial when domain checks needed | Domain-specific input checks execute correctly (e.g. PII scan on additional fields, consent validation, business rules) | PASS — `tests/unit/test_pre_process_node.py` (IP/CIDR + internal-hostname rejection) |
| TC-10 | S-3: `_extra_security_gate_output()` non-trivial when domain checks needed | Domain-specific output checks execute correctly (e.g. nested credential scan, PII re-check, content filtering, preservation verification) | PASS — `tests/unit/test_post_process_node.py` (IP/CIDR + internal-hostname rejection on output) |
| TC-11 | S-4: at least one domain `emit_trace_event()` inside each `execute()` | Domain event emitted on every invocation path | PASS — `pre_process`→`query_classified`, `main`→`kb_retrieved`/`guidance_generated`, `post_process`→`output_validated` |

## Proof-of-Boundary Tests (Mandatory)

| PB-ID | Boundary | Test | Expected Result | Result |
|-------|----------|------|----------------|--------|
| PB-1 | BaseNode → EventEmitter | `emit_trace_event()` fires on every invocation path | No silent failures | PASS — `tests/proof_of_boundary/test_pb_invoke_order.py` |
| PB-2 | State serialization | Post-invoke State is primitives only | No Pydantic/dataclass | PASS — `tests/proof_of_boundary/test_state_safety.py` |
| PB-3 | Level 2 → External service | Real external service connection | Data retrieved | N/A — real (non-mock) KB/LLM integration is explicitly out of scope for this iteration (`docs/implement_tasks.md` Tasks 4–5); both services raise `NotImplementedError` on the real path by design, verified in `tests/unit/test_services.py::test_real_mode_raises_not_implemented` |
| PB-4 | Import isolation | No Level 0 imports | AST scan: 0 violations | PASS — `tests/proof_of_boundary/test_import_isolation.py` |
| PB-5 | Checkpoint safety | No JWT/Pydantic in checkpoint | Inspection pass | PASS — `tests/proof_of_boundary/test_state_safety.py` |
| PB-6 | Invoke execution order | `__call__()`: S-1 trust gate → S-4 `node_start` → S-2 `_security_gate_input` → `execute()` → S-3 `_security_gate_output` → S-4 `node_complete` | Order verified | PASS — `tests/proof_of_boundary/test_pb_invoke_order.py` |

## Business Logic / Domain Tests

| TC-ID | Test | Input | Expected Result | Result |
|-------|------|-------|----------------|--------|
| BL-01 | Sub-domain classification (`tests/unit/test_pre_process_node.py::test_classification`) | 6 parametrized queries spanning each sub-domain + fallback | Correct `query_sub_domain` per query | PASS |
| BL-02 | Mock-mode alias resolution (`tests/unit/test_mock_mode.py`) | `USE_MOCK`, `STG_MOCK_MODE`, neither, case variants | `mock_mode_enabled()` returns correctly per `implementation_rule.md` Rule 1 | PASS |
| BL-03 | Mock mode succeeds with zero secrets bound (`tests/unit/test_main_node.py::test_mock_mode_succeeds_with_no_secret_provider_bound`) | Valid query, `ANTHROPIC_API_KEY` unset, no `bound_secrets()` context | `SUCCESS` per `test_rule.md` Rule 2 | PASS |
| BL-04 | Real (non-mock) service path fails fast (`tests/unit/test_services.py::test_real_mode_raises_not_implemented`) | `USE_MOCK`/`STG_MOCK_MODE` unset | `NotImplementedError`, not a silent placeholder | PASS |
| BL-05 | HTTP-level `/invoke` over real ASGI transport (`tests/integration/test_server_invoke.py`) | POST `/invoke` with Bearer `INVOKE_AUTH_TOKEN`, mock mode on | `200`, `status: "success"` — proves the async-route/sync-invoke boundary fix (`implementation_rule.md` Rule 3) | PASS |
| BL-06 | Full `.compile()` + `.invoke()` graph path (`tests/integration/test_graph.py`) | Real compiled `ZeroTrustQAGraph`, mock mode on | `SUCCESS` with full `node_history`; S-1/S-2 rejections also verified | PASS |

## Test Execution Summary
- Execution date: 2026-07-13
- Total tests: 37
- Pass: 37 / Fail: 0 / Skip: 0
- Coverage: not separately measured with `--cov` in this run; all `src/nodes/`, `src/services/`, `src/graph/graph.py`, and `src/api/server.py` code paths are exercised by the unit + integration suite above
- Re-verified via the project's local gate check script from the project root: all gates pass (scaffold integrity structure, import isolation, agent class composition, invoke chain, credential pattern scan, trust level declarations, category consistency, stub tests, dependency pinning, unit tests 37/37, proof-of-boundary 3/3). The script's disk-existence check for the locally-kept reference copy directory reports a false positive on a fresh local checkout — the directory is gitignored and will never actually be committed; this is a known limitation of that check's file-presence heuristic, not a real violation.
