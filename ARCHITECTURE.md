# Architecture — LLM Vendors Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle.

The net-new work in this recipe is the **LLM vendor switchboard** in
`server/src/vendors.py`: a data-driven registry that builds any A4.1 LLM vendor
from a `SPECS` table. The agent reads `LLM_VENDOR` and swaps only the LLM leg of
the cascade; STT and TTS stay on the proven keyless configs. The default vendor
(`openai`) is Agora-managed (keyless), so no separate LLM service is needed.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs  (always key-less)
  │  POST /api/startAgent           → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with:
  │    llm = build_vendor(LLM_VENDOR)   # validates BYO creds here, in start()
  │    stt = DeepgramSTT(nova-3, en)
  │    tts = MiniMaxTTS(speech_2_6_turbo, English_captivating_female1)
  │    parameters: data_channel=rtm, enable_metrics=true,
  │                enable_error_message=true
  │    advanced_features: enable_rtm=true
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed, nova-3, en)
  │  text → <LLM_VENDOR> (default OpenAI, Agora-managed, keyless)
  │  reply → MiniMax TTS (managed)
  │  RTM events → browser:
  │    AGENT_STATE_CHANGED, AGENT_METRICS, AGENT_ERROR,
  │    MESSAGE_ERROR, TRANSCRIPT_UPDATED
  ▼
EventTimeline + annotated transcript in the web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## The vendor registry

`server/src/vendors.py` is a **data-driven switchboard**:

- `SPECS` maps each `LLM_VENDOR` value to a `VendorSpec(cls, creds, defaults,
  model_field)` — the SDK vendor class, its required credential env vars, the
  SDK-verified default config, and which field `LLM_MODEL` overrides.
- `build_vendor(name, env)` fills every required SDK field from `defaults`,
  applies the optional `LLM_MODEL` override, then pulls each credential from the
  environment. A missing credential raises a clear `ValueError` listing the env
  vars — construction never fails on a missing required SDK field.
- `available()` / `required_env(name)` expose the registry for tests and docs.

Entries with empty `creds` (only `openai`) are 🟢 keyless. The framework code is
identical across the sibling vendor recipes; only `CATEGORY` and `SPECS` differ.

## Why creds are validated in start(), not __init__

`Agent.__init__` only reads `LLM_VENDOR` (no credential check). The selected
vendor is built in `start()` via `build_vendor`. This keeps `/get_config` and the
managed docker smoke key-less even when a BYO `LLM_VENDOR` is selected — the call
only fails (with a clear error) once you actually start a conversation.

## Event surface

All events arrive over RTM. The web client uses `AgoraVoiceAI` from
`agora-agent-client-toolkit` to subscribe. Each event is appended to a
`TimelineEvent[]` buffer (capped at 50) and rendered by `EventTimeline`.

| SDK event | Kind | What it carries |
| --- | --- | --- |
| `AGENT_STATE_CHANGED` | `state` | `listening`, `thinking`, `speaking`, `idle` |
| `AGENT_METRICS` | `metric` | Stage type, metric name, value (ms) |
| `AGENT_ERROR` | `error` | Error type + message |
| `MESSAGE_ERROR` | `error` | RTM message error code + message |
| `TRANSCRIPT_UPDATED` | `turn` | Role (agent/user) + text snippet |

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session (builds the selected LLM) |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → LLM vendor: on the default `openai` vendor, an Agora-managed key
  (transparent to this recipe). For any BYO vendor, the credentials you supply in
  the environment are passed through in the vendor config.
