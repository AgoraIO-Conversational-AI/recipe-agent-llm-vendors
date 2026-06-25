---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: agent.llm-vendor
    name: LLM vendor selection via LLM_VENDOR + per-vendor builder in vendors.py
  - id: api.routes
    name: Browser-facing API routes (including GET /vendors for in-UI switcher)
  - id: web.conversation-ui
    name: EventTimeline, annotated transcript, and pre-call vendor dropdown
  - id: verification.contracts
    name: Contract, proxy, and local FastAPI smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate and all BYO vendor API keys stay in the Python backend.
  - id: vendor.registry-driven
    summary: LLM vendor selection is data-driven through REGISTRY in vendors.py; agent.py calls build_vendor(), never hard-codes a vendor.
  - id: vendor.creds-in-start
    summary: BYO vendor credentials are validated in start() via build_vendor(), not in __init__(), so /get_config stays key-less.
  - id: pipeline.fixed-stt-tts
    summary: Only the LLM leg is swappable; STT (DeepgramSTT nova-3 en) and TTS (MiniMaxTTS speech_2_6_turbo) stay on the proven keyless configs.
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID and AGORA_APP_CERTIFICATE are always required; LLM_VENDOR defaults to openai (keyless).
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, POST /api/stopAgent, and GET /api/vendors remain the browser-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
  - id: vendor.openai-keyless
    summary: The default openai vendor requires no LLM API key; it is Agora-managed.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **LLM vendors** quickstart: a cascading STT→LLM→TTS pipeline whose LLM leg is a runtime-switchable vendor registry, behind a Next.js web client.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers who want to swap LLM backends at runtime (or via env) in an Agora Conversational AI voice agent.
- Reuse model: clone, bind project, optionally set `LLM_VENDOR` + that vendor's key, run, then customize the vendor registry or browser UI.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- A data-driven LLM vendor registry (`REGISTRY` in `vendors.py`) covering nine A4.1 vendors; `build_vendor()` selects and constructs the chosen one.
- Fixed STT (`DeepgramSTT`, nova-3, en) and TTS (`MiniMaxTTS`, speech_2_6_turbo) legs; only the LLM leg is swappable.
- Next.js browser UI with a vendor dropdown, live EventTimeline (state/metric/error/turn events), and annotated transcript.
- GET `/vendors` backend route + browser `getVendors()` client for populating the in-UI switcher.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, and local FastAPI smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI integration from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `agent.llm-vendor` | `server/src/vendors.py` `REGISTRY` | Add a `build_<vendor>` function + a `REGISTRY` entry with the SDK class, required creds, and defaults. | Run `verify:backend` + `cd server && pytest tests -v`; add vendor to `server/.env.example` comments. |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize EventTimeline, pre-call vendor dropdown, transcript, or metrics panels. | Preserve RTC/RTM lifecycle ownership and `TimelineEvent` import from `EventTimeline.tsx`. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, `/api/stopAgent`, and `/api/vendors` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, and all BYO vendor API keys.
- `build_vendor(name)` is called in `start()`, not `__init__()` — credentials are validated there.
- `openai` is the sole keyless vendor; all others require at least one credential env var.
- STT (`DeepgramSTT`) and TTS (`MiniMaxTTS`) stay on keyless configs; only the LLM leg changes.
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` |
| Optional backend env | `LLM_VENDOR` (default `openai`), `LLM_MODEL` (per-vendor default), `AGENT_GREETING` |
| BYO vendor env | One or more vendor-specific keys; see `required_env(name)` or `server/.env.example` |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, vendor?, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.vendor`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| `GET /api/vendors` | Returns `data.default` (current `LLM_VENDOR`), `data.vendors[]` (`name`, `needs_key`, `required_env`). |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact default model names and vendor-specific parameter values, as long as they stay documented defaults.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, and commands.
- `L1/02_architecture.md` — request flow, vendor registry, and topology.
- `L1/05_workflows.md` — common modification workflows.
- `L1/06_interfaces.md` — route, rewrite, env, and vendor registry contracts.
- `L1/L2/vendor_registry.md` — full vendor registry detail and per-vendor config.
- `L1/L2/session_lifecycle.md` — RTC/RTM/session orchestration.
