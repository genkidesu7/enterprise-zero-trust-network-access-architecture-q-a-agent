# Template Design Specification

## Position in AgentCore Architecture

- **Agent Class**: ZeroTrustQAGraph
- **L1 Base**: AgentBaseGraph
- **Three-Layer Separation**:
  - State: flat TypedDict composition (no Pydantic — msgpack incompatible)
  - Node: L1 inheritance (Template Method: `execute(self, state: dict) -> dict` override only)
  - Graph: composition (`register_nodes()` for node substitution)

## Architecture Overview

Cat 1, single reusable capability: retrieval-augmented Q&A over a zero-trust
network access (ZTNA) architecture knowledge base. The 5 conceptual steps from
the approved proposal (Query Classify, KB Retrieve, Context Enrich, Guidance
Generate, Output Validate) map onto the framework-owned 3-slot Cat 1 pipeline
as follows: `pre_process` performs classification, `main` performs retrieval +
enrichment + generation (via services), `post_process` performs validation and
disclaimer framing.

### Node Configuration

| Node | Responsibility | Input State | Output State | Inherits/Overrides |
|------|---------------|-------------|--------------|-------------------|
| initialize | Sets schema_version, session_id, caller_trust_level | — | — | InitializeNode (default) |
| pre_process | Validate `user_input`; classify into a ZTNA sub-domain (identity-aware proxy / microsegmentation / device trust / policy design / migration) | `user_input`, `input_context` | `validated_input`, `query_sub_domain`, `status` | FunctionNode |
| main | Retrieve KB chunks for `query_sub_domain` + `validated_input`; enrich with caller-supplied infra/compliance/team-maturity context; synthesize guidance via LLM | `validated_input`, `query_sub_domain`, `input_context` | `kb_chunks`, `infra_context`, `guidance_draft`, `result`, `status` | FunctionNode |
| post_process | S-3 gate (automatic) + domain check: strip any topology/credential-shaped content; attach advisory disclaimer | `result`, `guidance_draft` | `formatted_output`, `status` | FunctionNode |
| finalize | Builds response_metadata, total_time_ms | — | — | FinalizeNode (default) |

### Data Flow

```
START → initialize → pre_process → main → {route} → post_process → finalize → END
                                            ↓ (retry)
                                          pre_process
```

`main` returns `AgentStatus.RETRY` if KB retrieval yields zero chunks for a
classified sub-domain (routes back to `pre_process`, up to `max_retry`, so a
transient KB/service hiccup — not a genuine "no answer" — gets one more
classification pass); `AgentStatus.ERROR` for a real LLM/service failure to
short-circuit to `finalize`.

### State Definition

| Field | Type | Purpose | Required |
|-------|------|---------|----------|
| `query_sub_domain` | `str` | ZTNA sub-domain classified by `pre_process` (one of `identity_aware_proxy`, `microsegmentation`, `device_trust`, `policy_design`, `migration_sequencing`, or `general` fallback) | Yes, set by `pre_process` |
| `kb_chunks` | `list[dict]` | Retrieved KB chunks (`{"content": str, "source": str, "score": float}`), set by `main` | Yes, set by `main` |
| `infra_context` | `dict` | Caller-supplied infra/compliance/team-maturity context pulled from `input_context`, set by `main` | No (defaults to `{}`) |
| `guidance_draft` | `str` | Raw LLM-synthesized recommendation before disclaimer framing, set by `main` | Yes, set by `main` on SUCCESS |

**State Constraints (mandatory):**
- Flat TypedDict only (primitives + JSON-serializable types)
- No JWT, API keys, credentials in State (checkpoint DB leakage)
- InvocationContext via `config["configurable"]` only (not in State)
- No Pydantic models, dataclass, arbitrary Python objects (msgpack incompatible)

## Framework Utilization

### Shared Components Used
- [x] InvocationContext (correlation_id, session_id, permissions, credential handle) — `main` node resolves the LLM credential handle via `InvocationContext.credential_handle` from `config["configurable"]`
- [ ] ConnectionPolicy (retry/timeout strategy) — not needed; KB/LLM calls use the shared service defaults
- [x] SecurityViolationError — surfaced automatically by the framework `_security_gate_input`/`_security_gate_output` on PII/credential matches
- [x] S-2: `_extra_security_gate_input()` — domain-specific input check hook
      (`pre_process_node.py`: rejects `user_input` containing raw IP/CIDR or
      internal-hostname-shaped tokens before they reach the LLM prompt, since
      those are exactly the "internal network topology" data the proposal
      says must never enter the pipeline)
- [x] S-3: `_extra_security_gate_output()` — domain-specific output check hook
      (`post_process_node.py`: scans `formatted_output` for IP/CIDR/hostname
      patterns per the proposal's "no internal network topology or credential
      data ever enter output" requirement, in addition to the framework's
      default credential-pattern scan)
- [x] S-4: `emit_trace_event()` — at least one domain-specific event inside each `execute()`
      (`pre_process`: `query_classified`; `main`: `kb_retrieved` and
      `guidance_generated`; `post_process`: `output_validated`)

> **S-2/S-3 gate behaviour by node type (ADR-017):**
> - `FunctionNode` subclass → framework `@final` gate always runs automatically;
>   extend via `_extra_security_gate_input()` / `_extra_security_gate_output()` only
> - `GraphNode` / `RemoteAgentNode` → deliberate no-op (upstream or remote node's gate already applied)
> - Custom `BaseNode` subclass → must implement `_security_gate_input()` and
>   `_security_gate_output()` directly (`@abstractmethod` — omission raises `TypeError` at instantiation)

### Composition Pattern

- **Pattern**: Standalone (fixed 3-slot Cat 1 pipeline; no `GraphNode`/`RemoteAgentNode` composition)
- **Composition target**: N/A
- **Error propagation strategy**: propagate — KB/LLM service errors raised inside `main.execute()` are caught by the node and turned into `AgentStatus.ERROR` with a message in `error_log`; nothing is swallowed silently

## Services

- **`src/services/kb_retrieval_service.py`** (`KBRetrievalService`): cosine-similarity
  search over the zero-trust KB (NIST SP 800-207, BeyondCorp, ZTNA vendor docs) scoped
  by `query_sub_domain`; mock mode (`mock_mode_enabled()`) returns fixture chunks from
  `mock_data.py` with no external dependency.
- **`src/services/guidance_generation_service.py`** (`GuidanceGenerationService`): LLM
  call that synthesizes the architecture/policy recommendation from `validated_input` +
  `kb_chunks` + `infra_context`; mock mode returns a deterministic stub string. Real mode
  resolves the LLM credential via `InvocationContext.credential_handle`, never a raw key.
- **`src/services/mock_mode.py`** (`mock_mode_enabled()`): single shared helper checking
  both `USE_MOCK` (canonical) and `STG_MOCK_MODE` (what `deploy-stg` actually sets) —
  see `implementation_rule.md` Rule 1. Every service above imports this helper; no
  service re-derives its own mock-mode check.

## Import Isolation Confirmation
- [x] Template does not import agenticstar-platform SDK (Level 0)
- [x] Import targets: framework/ and shared/ only (no agents/base/ required)

## Design Decision Record

| Decision | Option A | Option B | Chosen | Rationale |
|----------|----------|----------|--------|-----------|
| L1 base type | AgentBaseGraph | AutonomousBaseGraph | AgentBaseGraph | Fixed retrieve→enrich→generate→validate pipeline, no self-directed reasoning loop — matches Cat 1 judgment in `docs/01_proposal.md` |
| Composition pattern | Standalone 3-slot | GraphNode subgraph | Standalone 3-slot | Single technical capability (Q&A), not a multi-step job-to-be-done requiring an inner domain workflow graph |
| KB retrieval location | Inside `main` node directly | Dedicated `KBRetrievalService` | `KBRetrievalService` | Keeps `main_node.py` thin (Template Method contract) and makes retrieval independently testable/mockable |
| Sub-domain classification | LLM call in `pre_process` | Keyword/rule-based classifier in `pre_process` | Rule-based classifier | Deterministic, zero extra LLM cost/latency for a 5-way classification task; falls back to `general` on no match (PB-3-style graceful degradation) |
