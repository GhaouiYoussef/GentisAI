# GentisAI Launch Demos Design

**Date:** 2026-07-22
**Status:** Approved for implementation planning
**Target release:** 0.2.1

## Objective

Ship a backward-compatible GentisAI framework patch and two polished Streamlit proof-of-concept applications for the next release announcement. The demos must make explicit routing, hybrid expert execution, sessions, streaming, tool execution, and provider switching understandable within the first ten seconds of a launch video.

The published `gentis-ai` 0.2.0 wheel, current PyPI documentation, and repository source at commit `08a7678` establish the API baseline. The release currently supports Python 3.10+, `Expert`, `Router`, `Flow`, structured `RoutingDecision` values, in-memory and SQLite sessions, streaming events, hybrid routing, provider adapters, and separate tool primitives.

## Verified Baseline And Limitations

- Installation is `pip install gentis-ai`; OpenAI-compatible support is installed with `pip install "gentis-ai[openai]"`.
- `Flow.stream_turn()` streams tokens for single-expert routes, but hybrid routes currently return only a final synthesized event.
- Hybrid execution does not emit `expert_started` events for every consulted expert.
- `ToolRegistry` and `ToolExecutor` execute safe registered Python functions, but `Flow` does not currently integrate tool execution or emit the declared `tool_call` and `tool_result` events.
- Provider adapters do not share a complete autonomous tool-calling loop. The launch patch will not invent one.
- Routing confidence may be displayed only when returned by `RoutingDecision`; latency will be measured with `time.perf_counter()`; token usage will be displayed only when the provider reports a non-zero value.

## Chosen Approach

Implement a launch-scoped framework patch before building the demos. GentisAI will own routing, explicit application-authorized tool execution, events, expert execution, synthesis, and session persistence. It will not add hidden manager loops or autonomous repeated tool selection.

The demos will use the framework's real event stream without fabricating expert activity, confidence, tool calls, latency, token usage, or memory behavior.

## Framework Patch

### Public Types

Add a typed `ToolCall` model with:

- `name: str`
- `arguments: dict[str, Any]`

Export `ToolCall` through `gentis_ai.tools` and the top-level package. Keep the existing `ToolSpec`, `ToolResult`, `ToolRegistry`, and `ToolExecutor` APIs unchanged.

Define an application-owned tool policy contract:

```python
ToolPolicy = Callable[[str, RoutingDecision], list[ToolCall]]
```

The policy receives the original user message and validated routing decision. It returns only application-authorized calls. This makes business policy explicit and avoids text regexes or an autonomous LLM tool loop.

### Flow Construction

Append these optional parameters to `Flow.__init__()` so existing positional and keyword calls remain valid:

```python
tool_executor: ToolExecutor | None = None
tool_policy: ToolPolicy | None = None
```

Both must be configured for automatic per-turn tool execution. Configuring only one raises a clear `ValueError` during construction rather than failing silently at runtime.

### Unified Turn Pipeline

Refactor synchronous turn handling around one internal event generator consumed by both `process_turn()` and `stream_turn()`:

1. Resolve and load the explicit session.
2. Emit `route_started`.
3. Classify the original user message and emit `route_finished`.
4. Ask the configured tool policy for authorized calls.
5. Reset the tool executor's per-turn counter once.
6. Execute each call and emit `tool_call` followed by `tool_result`.
7. Build clearly delimited, provider-neutral tool context from successful results and safe failure summaries.
8. Execute the single expert or hybrid expert set.
9. Stream final response tokens.
10. Update and save session history once.
11. Emit `final` with the same `TurnResponse` returned by `process_turn()`.

When tools are not configured, behavior remains identical to 0.2.0.

### Tool Safety And Context

- The existing registry remains the allowlist; unknown tools raise `ToolExecutionError` and produce an `error` event with a safe public message.
- Approval-required results emit `tool_result` with `approval_required=True` and are not presented to the model as successful data.
- Tool exceptions and timeouts retain safe `ToolResult` behavior.
- Tool output is serialized into a labeled context block and passed to generation without modifying the original user message stored in history.
- `TurnResponse.structured["tools"]` contains serializable tool result metadata for the UI.
- Callback hooks receive matching tool start/end notifications.

### Hybrid Streaming

For hybrid routes:

- Emit `expert_started` once for every selected expert before consultation begins.
- Preserve `parallel_execution=True` behavior for independent consultations.
- Collect consultation text internally and use the default expert as synthesizer.
- Emit `expert_started` for the synthesizer when it is not already one of the selected experts.
- Call the provider with `stream=True` for synthesis and emit each chunk as a `token` event.
- Store only the original user message and final synthesized answer in ordinary conversation history.
- Include the validated routing decision and tool metadata in the final structured response.

If one consultant fails, retain the existing safe per-expert fallback and allow synthesis to continue. If synthesis fails, emit an `error` event and the existing generic safe response.

### Async Behavior

`aprocess_turn()` and `astream_turn()` continue to wrap the synchronous pipeline. They require no separate business logic and must produce the same event order and final response semantics.

### Framework Verification

Tests will cover:

- backward-compatible construction and single-expert behavior;
- identical final responses from process and stream APIs;
- hybrid `expert_started`, streamed token, and final event ordering;
- parallel hybrid consultation without flaky wall-clock assertions;
- tool policy execution after routing;
- tool call limits, approvals, unknown tools, timeouts, and exceptions;
- callback parity for tool and expert events;
- tool metadata serialization;
- session history updates exactly once;
- session isolation across explicit IDs;
- async parity with the synchronous pipeline.

## Demo Comparison

| POC | Target audience | Problem solved | GentisAI features | Visual hook | Video value | Complexity |
|---|---|---|---|---|---|---|
| Customer Rescue Command Center | Support and CX engineering teams | Coordinate mixed customer issues without calling every specialist | Explicit routing, hybrid experts, sessions, streaming, tools, confidence, provider switching | Expert cards activate while invoice and ticket events appear | A complex message produces an understandable rescue team and response immediately | Medium |
| AI Product Launch War Room | Founders and product engineering teams | Get focused launch advice from only the relevant disciplines | Contextual routing, parallel hybrid execution, synthesis, sessions, streaming, provider switching | Different expert cards activate for risk, copy, feasibility, and full-plan prompts | Repeated prompts visibly prove that routing is contextual rather than broadcast | Medium |

## Shared Demo Principles

- Python 3.10+ and Streamlit.
- Three or fewer main Python source files per POC.
- Offline deterministic mode uses the published `MockLLM` API and requires no key.
- Real mode uses `OpenAICompatibleLLM` with `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and configurable `OPENAI_MODEL`.
- Environment variables are read directly; the applications do not load `.env` files.
- Each app keeps its `Flow` and explicit session IDs in `st.session_state` so Streamlit reruns do not erase memory.
- The interface displays only actual routing decisions, events, elapsed time, and provider-reported usage.
- A visible provider badge distinguishes deterministic mock output from real model output.
- CSS uses an editorial control-room visual language with warm off-white surfaces, ink/navy structure, signal orange, teal status accents, and expressive non-default typography with offline-safe fallbacks.
- Desktop uses a three-zone layout; mobile collapses to expert cards, conversation, then event timeline.
- Errors appear as friendly setup or provider messages while internal exception details remain in logs.

## POC 1: Customer Rescue Command Center

### Product Definition

**Hook:** One customer message assembles the exact rescue team, runs safe account tools, and streams a coordinated answer.

**Target user:** Customer experience engineers, support platform teams, and technical buyers evaluating multi-expert routing.

**Core journey:** Select or create a session, enter a customer message, watch expert cards activate, observe tool events, read the streamed answer, then ask a follow-up in the same session.

**Memorable moment:** The message "I was charged twice, the application keeps crashing, and I'm thinking of cancelling" activates Billing, Technical Support, and Customer Retention while a fictional invoice check and support ticket appear in the event rail.

### Experts And Routing

- `technical_support`: crashes, errors, troubleshooting, and incident handling.
- `billing`: invoices, duplicate charges, refunds, and payment questions.
- `sales`: plans, upgrades, features, and purchase intent.
- `account_security`: suspicious access, password resets, and account protection.
- `customer_retention`: cancellations, dissatisfaction, and recovery offers.
- `customer_rescue_lead`: default expert and hybrid synthesizer.

Mock routing rules return single expert names or explicit expert lists. Real routing uses the same `Router` and expert descriptions. The tool policy derives authorized calls from the validated selected experts, not text pattern matching.

### Tools

- `lookup_account(account_ref: str)`: returns a fictional account summary.
- `check_invoice(invoice_ref: str)`: returns a fictional invoice and duplicate-charge status.
- `create_support_ticket(account_ref: str, issue: str)`: creates an in-memory fictional ticket with a deterministic ID in mock mode.

Billing authorizes `check_invoice`, Technical Support authorizes `create_support_ticket`, and Account Security authorizes `lookup_account`. Tool inputs come from the selected fictional customer record held by the application, never from secrets or external systems.

### Interface

- Header: product name, provider badge, active session, and reset control.
- Expert strip: six cards with idle, selected, consulting, and synthesizing states.
- Main conversation: customer messages and streamed assistant response.
- Event rail: routing mode, confidence when available, tool calls/results, expert activity, measured elapsed time, and usage when reported.
- Scenario chips: single Billing, hybrid rescue, and memory follow-up prompts.

### Files

```text
demos/customer_rescue/
|-- app.py
|-- gentis_setup.py
|-- tools.py
|-- requirements.txt
|-- .env.example
|-- README.md
`-- tests/test_customer_rescue.py
```

## POC 2: AI Product Launch War Room

### Product Definition

**Hook:** A founder asks one launch question and only the relevant product team enters the room.

**Target user:** Founders, indie hackers, developer marketers, and product engineers.

**Core journey:** Enter a product brief, ask a focused launch question, watch contextual expert selection and streamed synthesis, then ask a follow-up in the same session.

**Memorable moment:** Risk, hook-writing, feasibility, and complete-recommendation prompts activate visibly different expert combinations without changing application code.

### Experts And Routing

- `product_strategist`: positioning, target user, prioritization, and default synthesis.
- `growth_marketer`: channels, acquisition, launch mechanics, and hooks.
- `technical_architect`: feasibility, scope, systems, and delivery trade-offs.
- `risk_analyst`: product, market, operational, and adoption risk.
- `financial_analyst`: pricing, costs, runway, and unit economics.
- `copywriter`: headlines, launch copy, and concise messaging.

Mock rules cover the documented scripted scenarios with deterministic expert lists. Real mode uses the same expert descriptions and structured router output. This POC does not add subjective scoring tools; it focuses on contextual routing and synthesis.

### Interface

- Header: war-room title, provider badge, active session, and measured timer.
- Brief panel: persistent product idea or feature description.
- Expert grid: six cards that visibly activate from routing and expert events.
- Recommendation panel: streaming final output with route summary.
- Timeline: route started, selected experts, synthesis, completion, confidence when available, and provider usage when reported.
- Scenario chips: risks, launch hooks, weekend feasibility, complete recommendation, and follow-up.

### Files

```text
demos/launch_war_room/
|-- app.py
|-- gentis_setup.py
|-- requirements.txt
|-- .env.example
|-- README.md
`-- tests/test_launch_war_room.py
```

## Launch Material

Create `docs/launch/gentisai-0.2.1-launch-kit.md` containing:

- the final comparison table;
- detailed product and architecture descriptions;
- Mermaid diagrams for both POCs;
- exact project trees and setup commands;
- three scripted interactions per POC covering single route, hybrid route, and session-memory follow-up;
- verification instructions and runtime troubleshooting;
- a 75-90 second timestamped storyboard with voice-over, on-screen action, on-screen text, and transitions;
- five video titles and five opening hooks of at most twelve words;
- one X post, one technical LinkedIn post, one Hacker News description, and one GitHub README demo section;
- a launch-readiness checklist.

The material must state that 0.2.1 uses explicit application-owned tool policies and streams the final hybrid synthesis. It must not claim autonomous tool selection, fabricated benchmark improvements, or deterministic real-provider wording.

## Installation And Versioning

The framework patch is backward-compatible and increments the project version from 0.2.0 to 0.2.1. Before publication, repository-local setup uses:

```bash
python -m venv .venv
python -m pip install -e ".[openai,dev]"
python -m pip install streamlit
```

After 0.2.1 is published, each demo requirements file uses:

```text
gentis-ai[openai]>=0.2.1,<0.3
streamlit>=1.36,<2
```

Mock mode is the default. Real mode requires `GENTIS_PROVIDER=openai` and `OPENAI_API_KEY`; optional variables configure base URL and model. Missing provider dependencies or credentials produce actionable UI messages.

## Error Handling

- Router or provider failures use GentisAI's existing generic safe response and emit an error event.
- Tool failures show the tool name and safe error state without stack traces.
- A malformed tool policy result raises a typed, logged configuration error.
- Empty messages are rejected in the Streamlit UI with a concise prompt.
- Session reset creates a new explicit ID and clears only that app's displayed conversation.
- A real-provider setup failure does not silently fall back to mock mode; the UI explains how to switch deliberately.

## Acceptance Criteria

- The full existing test suite remains green.
- New framework tests prove streaming and tool event behavior without real network calls.
- Each POC starts in mock mode with one documented Streamlit command.
- Each POC passes smoke, routing, and session-isolation tests.
- The showcase hybrid prompt produces more than one actual selected expert.
- Hybrid synthesis emits at least one token event before the final event in mock and compatible real-provider modes.
- Tool events correspond to real `ToolExecutor` results.
- A follow-up reuses the same explicit session and prior message history.
- Switching sessions does not leak displayed messages or framework history.
- No API key or secret is committed.
- No latency, confidence, token, or benchmark value is fabricated.
- Both apps remain usable at desktop and mobile widths.
- The launch kit contains every requested video and social deliverable.

## Out Of Scope

- Autonomous multi-step tool calling or provider-specific tool-call parsing.
- External CRM, billing, ticketing, analytics, or database integrations.
- User authentication and production multi-tenant persistence for the demos.
- New agent frameworks or orchestration dependencies.
- Benchmark claims not reproduced during this implementation.
- Publishing the package to PyPI or deploying the Streamlit applications.
