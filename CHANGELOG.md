# Changelog

## 0.2.1

- Load local .env settings in demos and provider templates with shell overrides.
- Support Azure aliases, full deployment URLs, explicit API versions, and
  GPT-5-compatible completion token budgets.

- Refresh demo expert cards and traces during generation, expose fictional tool
  results, and retain measured latency after reruns.
- Return generic tool failures and redact UUIDs, emails, and Bearer tokens in
  configured logs, including tracebacks.
- Clarify source-checkout setup, scripted mock behavior, and deployment boundaries.
- Add typed, application-owned tool policies and real tool call/result events.
- Stream hybrid synthesis while exposing selected expert activity.
- Unify process and stream turn behavior with session-safe history updates.
- Add Customer Rescue and Product Launch Streamlit demos with offline mock mode.
- Add launch-video, social, setup, and verification material.

## 0.2.0

- Make core install lightweight with provider extras.
- Add default expert system prompts and strict internal message roles.
- Add structured `RoutingDecision` results and deterministic keyword routing.
- Add explicit sessions with in-memory and SQLite stores.
- Add event-based streaming APIs and async turn APIs.
- Add tool spec, registry, executor, callback hooks, metrics, and JSON logging.
- Add optional LangGraph bridge.
- Add CLI templates and release hygiene files.

## 0.1.x

- Early routing, flow, memory, and provider adapter prototypes.
