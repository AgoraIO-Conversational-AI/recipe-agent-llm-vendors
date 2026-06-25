# 02 · Architecture

> Two co-located processes. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The backend owns Agora tokens, the agent session, and a data-driven LLM vendor registry — swapping only the LLM leg while STT and TTS stay on proven keyless configs.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds: DeepgramSTT + build_vendor(LLM_VENDOR) + MiniMaxTTS
                                 │  parameters: data_channel=rtm, enable_metrics=true,
                                 │              enable_error_message=true
                                 │              advanced_features: enable_rtm=true
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → Deepgram STT (managed, nova-3, en)
                                 │  text → <LLM_VENDOR> (default OpenAI, Agora-managed, keyless)
                                 │  reply → MiniMax TTS (managed)
                                 │  RTM events → browser
                                 ▼
                              EventTimeline + annotated transcript in the web UI
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI, vendor dropdown, RTC/RTM client lifecycle, EventTimeline, annotated transcript. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- No `llm/` service, no mock vendor — on the default `openai` vendor the LLM is Agora-managed.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs. Always works key-less.
2. Browser fetches `GET /api/vendors` to populate the LLM dropdown; returns list with `needs_key` flag per vendor.
3. Browser joins the RTC channel, then `POST /api/startAgent { vendor? }`; backend calls `build_vendor(selected)` which validates BYO creds, builds the LLM, and starts an async agent session.
4. Agora routes user audio through Deepgram STT → selected LLM → MiniMax TTS; the agent's reply enters the channel.
5. RTM emits `AGENT_STATE_CHANGED`, `AGENT_METRICS`, `AGENT_ERROR`, `MESSAGE_ERROR`, `TRANSCRIPT_UPDATED` events to the web UI. Each becomes a `TimelineEvent` (capped at 50).
6. `POST /api/stopAgent { agentId }` ends the session.

## The vendor registry

`server/src/vendors.py` is a data-driven switchboard:

- `REGISTRY` maps each `LLM_VENDOR` string to a `(builder, required_creds)` tuple.
- `build_vendor(name, env)` checks creds, then calls the matching `build_<vendor>(env)` function, raising a clear `ValueError` listing any missing env vars.
- `available()` / `required_env(name)` / `needs_key(name)` expose the registry for tests, docs, and the `/vendors` route.

The builder functions are intentionally readable, copy-pasteable SDK constructor examples.

## Why creds are validated in `start()`, not `__init__()`

`Agent.__init__` reads only `LLM_VENDOR` (no credential check). `build_vendor()` is called in `start()`. This keeps `GET /get_config` and the managed docker smoke key-less even when a BYO `LLM_VENDOR` is selected — the call only fails (with a clear error) once the conversation starts.

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; reads `LLM_VENDOR`, calls `build_vendor()` in `start()`, keeps `_sessions` map.
- **`REGISTRY`** (`server/src/vendors.py`) — nine vendor entries; `build_vendor()` is the single build entry point.
- **`EventTimeline`** (`web/src/components/EventTimeline.tsx`) — renders the live `TimelineEvent[]` buffer; exports the `TimelineEvent` type (import from here, not a separate types file).
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed (set `AGENT_BACKEND_URL`).
- **Fixed STT + TTS, swappable LLM** — only the reasoning leg changes; STT and TTS stay on proven Agora-managed keyless configs.
- **In-UI vendor switcher** — `GET /vendors` + dropdown let you change the LLM without restarting; the backend validates creds only at `startAgent`.

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — full REGISTRY detail, per-vendor config, and adding/changing a vendor.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + vendor fetch + start/stop, RTC/RTM, EventTimeline.
