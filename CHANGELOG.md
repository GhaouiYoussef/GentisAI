# Changelog

## 0.2.32

- Assign demo tools explicitly per agent, with ticket creation initially limited
  to Technical Support. Grant Billing the same tool by editing `AGENT_TOOLS`.
- Create new demo ticket IDs from the actual customer issue and ground offline
  replies in successful tool results, including clear missing-tool messages.
- Add an agent selector and visible assignments for permission demonstrations.
- Load optional provider SDKs only when requested, reducing demo and CLI startup.
- Cover ticket permissions, agent reassignment, Streamlit interaction, and lazy
  provider imports with regression tests.

## 0.2.31

- Export complete, editable Streamlit demos with `gentis demo --export`.
- Scaffold modular agents, tools, prompts, and a Streamlit app with `gentis init`.
- Register new components with `gentis add agent` and `gentis add tool`.
- Launch local Streamlit apps with `gentis run --ui`.
- Provide a secret-free `.env.example` while preserving existing configuration.
- Add in-app CLI guidance, immediate component reloads, and generated-project tests.
- Verify exported demos and modular starters from the installed wheel.

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
