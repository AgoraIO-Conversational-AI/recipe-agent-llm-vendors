# Agora Agent Backend — LLM Vendors Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the LLM vendors recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

Starts a conversational AI agent whose **LLM leg is selected at runtime** from a
data-driven registry (`src/vendors.py`), while keeping the STT and TTS legs on the
proven keyless configs. It also enables the three flags that drive the web event
surface:

- `data_channel = "rtm"` — routes all events over RTM to the browser
- `enable_metrics = True` — emits per-stage latency (STT, LLM, TTS)
- `enable_error_message = True` — surfaces agent and message errors over RTM

**Pipeline:** `DeepgramSTT(nova-3, en)` → `<LLM_VENDOR>` (default `openai`, Agora-managed, keyless) → `MiniMaxTTS`

The default `openai` vendor is Agora-managed (keyless), so the recipe is
**zero-key** out of the box. There is **no separate `llm/` service**.

## The vendor registry

`src/vendors.py` is a data-driven switchboard:

- `SPECS` maps each `LLM_VENDOR` value to `VendorSpec(cls, creds, defaults, model_field)`.
- `build_vendor(name, env)` builds the vendor, raising `ValueError` listing any
  missing credential env vars.
- `required_env(name)` / `available()` expose the registry.

`agent.py` reads `LLM_VENDOR` in `__init__` (no validation) and calls
`build_vendor(self.vendor)` in `start()` — so BYO credentials are validated only
when a conversation starts, and `/get_config` stays key-less.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work on
this module directly:

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/server.py
```

## Environment

Required:

- `AGORA_APP_ID` — Agora project App ID.
- `AGORA_APP_CERTIFICATE` — Agora project App Certificate.

Optional:

| Variable | Default | Notes |
| --- | :---: | --- |
| `LLM_VENDOR` | `openai` | Which LLM vendor to build (see the root README Vendors table) |
| `LLM_MODEL` | per-vendor | Optional model override for the selected vendor |
| `AGENT_GREETING` | built-in | Optional opening line override |

Selecting a BYO `LLM_VENDOR` additionally requires that vendor's credential env
vars (see `required_env` in `src/vendors.py` and the root README). These are
validated when the agent starts, not at construction.

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session (builds the selected LLM)
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
