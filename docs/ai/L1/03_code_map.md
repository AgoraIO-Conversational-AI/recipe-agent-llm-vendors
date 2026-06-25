# 03 · Code Map

> Where things live. Two top-level modules: `web/` (Next.js client) and `server/` (FastAPI backend). Orchestration is in the root `package.json`.

## Root

| Path                  | Responsibility                                                              |
| --------------------- | --------------------------------------------------------------------------- |
| `package.json`        | Bun workspace; `setup`, `dev`, `doctor*`, `verify*`, `clean` scripts.       |
| `README.md`           | Setup, vendor table, run modes, env, troubleshooting.                       |
| `ARCHITECTURE.md`     | System shape, vendor registry design, event surface.                        |
| `AGENTS.md`           | Coding-agent handbook + How to Load / Git Conventions / Doc Commands.       |
| `Dockerfile`          | Backend-only image (`:8000`).                                               |
| `.github/workflows/`  | `ci.yml` (backend pytest matrix + web verify), `docker.yml`, `nightly.yml`. |

## `server/` — FastAPI backend (:8000)

| Path                              | Responsibility                                                               |
| --------------------------------- | ---------------------------------------------------------------------------- |
| `src/server.py`                   | FastAPI app, CORS, route handlers, error mapping, `/vendors` route, uvicorn entrypoint. |
| `src/agent.py`                    | `Agent` class: `AsyncAgora` client, `start()`/`stop()`, `_sessions`.         |
| `src/vendors.py`                  | `REGISTRY` + nine `build_<vendor>()` functions + `build_vendor()` / `required_env()` / `available()` / `needs_key()`. |
| `scripts/run_fake_server.py`      | Boots `server.app` with a `FakeAgent` for the local FastAPI smoke test.      |
| `tests/test_vendors.py`           | Constructs every vendor with dummy creds; asserts BYO-missing-cred error.    |
| `tests/test_agent_construction.py`| Builds real `AgoraAgent`, fakes the SDK session, asserts start shape.        |
| `tests/test_agent_config.py`      | Agent constructs with defaults; `vendor == "openai"` when `LLM_VENDOR` unset.|
| `tests/conftest.py`               | `fake_env` fixture; no cloud, no real creds.                                 |
| `.env.example`                    | Env template with all nine vendor blocks commented out (do not add `PORT`).  |
| `requirements*.txt`               | Runtime + dev (pytest) deps.                                                 |

## `server/src/server.py` routes

- `GET /get_config` — token + channel/UID config.
- `GET /vendors` — list all registered LLM vendors with `needs_key` and `required_env`.
- `POST /startAgent` — start the agent with the selected LLM vendor.
- `POST /stopAgent` — stop by `agent_id`.

## `web/` — Next.js client (:3000)

| Path                                       | Responsibility                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------- |
| `next.config.ts`                           | `/api/*` rewrites to `AGENT_BACKEND_URL`; strict mode; Turbopack root.          |
| `src/services/api.ts`                      | Browser API client: `getConfig`, `getVendors`, `startAgent`, `stopAgent`.       |
| `src/lib/conversation.ts`                  | Transcript normalization, timestamp/UID mapping, visualizer state.              |
| `src/lib/agora.ts`                         | Agora RTC/RTM helpers; exports `DEFAULT_AGENT_UID`.                             |
| `src/components/EventTimeline.tsx`         | Live EventTimeline; exports `TimelineEvent` type (import from here).            |
| `src/components/LandingPage.tsx`           | Conversation entry: config fetch, vendor fetch, agent start, RTM login, teardown. |
| `src/components/ConversationComponent.tsx` | RTC join, mic publish, RTM event → `TimelineEvent` append, transcript listeners. |
| `src/components/Quickstart*.tsx`           | Pre-call card (with vendor dropdown), transcript, metrics, layout panels.       |
| `scripts/verify-api-contracts.ts`          | Asserts rewrites + client paths + response envelope (no network).               |
| `scripts/verify-local-proxy.ts`            | Stub backend; proxies `/api/*` through the rewrite map.                         |
| `scripts/verify-local-fastapi.ts`          | Spawns real FastAPI with `FakeAgent`; proxies routes end-to-end.                |
| `scripts/verify-local-llm.ts`              | Smoke test for the vendor LLM leg (if a real LLM is reachable).                |
| `scripts/doctor.ts`                        | Web prerequisite check.                                                         |

## Related Deep Dives

- None. For runtime flow see [02_architecture](02_architecture.md); for contracts see [06_interfaces](06_interfaces.md).
