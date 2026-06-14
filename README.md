# Agora Conversational AI — LLM Vendors Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **LLM vendors** recipe in the Agora Conversational AI recipes family.
A voice assistant whose **LLM leg is a per-vendor switchboard** over every
A4.1 LLM vendor. It **runs zero-key on the default `openai` LLM** (Agora-managed,
no `OPENAI_API_KEY` required); set `LLM_VENDOR=<x>` plus that vendor's key to swap
in any other LLM. The STT and TTS legs stay on the proven keyless configs, so only
the reasoning leg changes.

**Pipeline:** `DeepgramSTT(nova-3, en)` → **`<LLM_VENDOR>`** (default `openai`, keyless) → `MiniMaxTTS`

## Vendors

Two ways to pick a vendor:
- **In the UI** — the pre-call screen has an **LLM vendor dropdown**; choose one and
  start. No restart needed. (A "needs key" vendor still requires its env vars set on
  the server; if they're missing, startup reports exactly which.)
- **By env** — set `LLM_VENDOR` (the default for the dropdown) + the vendor's key in
  `server/.env.local`; optionally override the model with `LLM_MODEL`.

| Vendor | `LLM_VENDOR` | Required env | Default model |
| --- | --- | --- | --- |
| OpenAI (managed) | `openai` 🟢 | _none_ | `gpt-4o-mini` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash` |
| Groq | `groq` | `GROQ_API_KEY` | `llama-3.3-70b-versatile` |
| Azure OpenAI | `azure` | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` |
| Amazon Bedrock | `bedrock` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` | `anthropic.claude-3-5-sonnet-20240620-v1:0` |
| Vertex AI | `vertexai` | `GOOGLE_API_KEY`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION` | `gemini-2.0-flash` |
| Dify | `dify` | `DIFY_API_KEY`, `DIFY_URL` | `dify` |
| Custom (OpenAI-compatible) | `custom` | `CUSTOM_LLM_API_KEY`, `CUSTOM_LLM_BASE_URL` | `gpt-4o-mini` |

🟢 = keyless default. The selected vendor's credentials are validated **when the
agent starts** (not at construction), so `/get_config` always works key-less.

### Sample code — how each vendor is wired

Every vendor is a small, copy-pasteable builder in [`server/src/vendors.py`](server/src/vendors.py)
that shows the real SDK constructor. For example:

```python
from agora_agent.agentkit.vendors import OpenAI, Anthropic, Groq

# OpenAI — Agora-managed, key-less:
OpenAI(model="gpt-4o-mini")

# Anthropic Claude — set ANTHROPIC_API_KEY:
Anthropic(
    api_key=env["ANTHROPIC_API_KEY"],
    model="claude-3-5-sonnet-20241022",
    url="https://api.anthropic.com",
    max_tokens=1024,
    headers={},
)

# Groq — set GROQ_API_KEY:
Groq(
    api_key=env["GROQ_API_KEY"],
    model="llama-3.3-70b-versatile",
    base_url="https://api.groq.com/openai/v1",
)
```

The agent attaches the chosen one with `.with_llm(build_vendor(name))`; STT
(`DeepgramSTT`) and TTS (`MiniMaxTTS`) stay on their key-less configs. To add or
change a vendor, edit its `build_<vendor>` function + the `REGISTRY` line.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy

## Run It

```bash
# 1. Install web deps + create the Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>          # select which project to use
agora project env write server/.env.local # writes App ID + Certificate

# 3. Run backend + web
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak.
Watch the **Event Timeline** panel update in real time.

To try a different LLM, pick it from the **dropdown** on the pre-call screen (no
restart). For a "needs key" vendor, set its key in `server/.env.local` first (see
[Vendors](#vendors)).

### Working from a clone

`bun run setup` creates the Python venv and installs web dependencies.
`bun run dev` brings up both services. You still need Agora credentials in
`server/.env.local` before a conversation can connect.

Services:

- Frontend — http://localhost:3000
- Backend — http://localhost:8000
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-llm-vendors` on `v*` tags.
It exposes **BACKEND-ONLY** (:8000). On the default `openai` vendor no separate
LLM container is needed — OpenAI is Agora-managed.

## Environment variables

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate |
| `LLM_VENDOR` | | `openai` | Which LLM vendor to use (see [Vendors](#vendors)) |
| `LLM_MODEL` | | per-vendor | Optional model override for the selected vendor |
| `AGENT_GREETING` | | built-in | Optional opening line override |
| _vendor creds_ | | — | Required only for the selected BYO vendor (see [Vendors](#vendors)) |

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session
                          │  LLM leg = build_vendor(LLM_VENDOR)
                          │  flags: enable_rtm=true, enable_metrics=true,
                          │         enable_error_message=true
                          ▼
                       Agora ConvoAI Cloud
                          │  Deepgram STT (managed, en)
                          │  <LLM_VENDOR> (default OpenAI, keyless)
                          │  MiniMax TTS (managed)
                          │  RTM events → browser
                          ▼
                       EventTimeline + annotated transcript in the web UI
```

The LLM vendor switchboard lives in `server/src/vendors.py` — one readable
`build_<vendor>` function per vendor (the sample code) plus a `REGISTRY` mapping
name → builder + required env. See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **vendor switchboard** for the LLM leg: one `build_vendor()` over a `SPECS`
  table covering all nine A4.1 LLM vendors, selected via `LLM_VENDOR`.
- A **Next.js** web client (:3000) with a live **EventTimeline** (state, metric,
  error, turn events; reverse-chronological, capped at 50) and an **annotated
  transcript** that shows the current agent state in the header.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the
  agent session lifecycle.
- **Zero-key by default** — the full pipeline runs with no LLM API key on the
  managed `openai` vendor.

## How It Works

1. The browser calls `/api/get_config`; the backend mints an Agora token. This
   works key-less even when a BYO `LLM_VENDOR` is selected — credentials are only
   checked at agent start.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   builds the selected LLM via `build_vendor(LLM_VENDOR)` (raising a clear error
   if a BYO vendor is missing its credentials) and starts the agent with
   `data_channel="rtm"`, `enable_metrics=True`, and `enable_error_message=True`.
3. The agent speaks with the user. Agora emits RTM events for every state change,
   per-stage metric, transcript turn, and error.
4. The web client's `AgoraVoiceAI` SDK receives these events and appends a
   `TimelineEvent` for each one (capped at 50).
5. `EventTimeline` renders the events in reverse-chronological order with a
   colored badge per kind. The transcript header shows the current agent state.
6. `/api/stopAgent` ends the session.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle, EventTimeline, transcript.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle.
- `server/src/vendors.py` — one readable builder per LLM vendor + the registry.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `LLM vendor '<x>' requires environment variable(s): ...` at start | Set the listed env vars for that `LLM_VENDOR` (see [Vendors](#vendors)), or switch back to `openai`. |
| No events appear in the timeline | Ensure `enable_rtm`, `enable_metrics`, `enable_error_message` are set (they are, by default in this recipe). |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
