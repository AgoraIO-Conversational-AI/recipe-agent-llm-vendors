# 01 · Setup

> Install dependencies, configure env, and run the LLM vendors recipe locally. This recipe is **zero-key by default** on the managed `openai` vendor; BYO vendor keys are only needed when you select a non-`openai` `LLM_VENDOR`.

## Prerequisites

- Python 3.10+ (backend runs on 3.10 and 3.13 in CI)
- [Bun](https://bun.sh/) (runs the web app and orchestration scripts)
- [Agora CLI](https://github.com/AgoraIO/cli) (optional; easiest way to mint App ID + Certificate)

## Install

```bash
bun run setup            # installs web deps + creates server/ venv from requirements.txt
```

`setup` runs `setup:env` (copies `server/.env.example` → `server/.env.local` if missing), `setup:server` (recreates `server/venv`, installs `requirements.txt`), and `setup:web` (`bun install`).

## Configure env

Backend env file is `server/.env.local` (template: `server/.env.example`).

| Variable                | Required | Default                               | Notes                                                     |
| ----------------------- | :------: | ------------------------------------- | --------------------------------------------------------- |
| `AGORA_APP_ID`          |    ✅    | —                                     | Agora Console → Project → App ID                          |
| `AGORA_APP_CERTIFICATE` |    ✅    | —                                     | Agora Console → Project → App Certificate                 |
| `LLM_VENDOR`            |          | `openai`                              | Which LLM vendor to build; `openai` is keyless            |
| `LLM_MODEL`             |          | per-vendor (e.g. `gpt-4o-mini`)       | Optional model override for the selected vendor           |
| `AGENT_GREETING`        |          | `Hi! Talk to me and watch the event timeline light up.` | Optional opening utterance override |
| _vendor creds_          |          | —                                     | Required only for the selected BYO vendor; see below      |

### BYO vendor keys (needed only for non-`openai` vendors)

| `LLM_VENDOR` | Required env vars |
| ------------ | ----------------- |
| `openai` 🟢  | _none_ |
| `anthropic`  | `ANTHROPIC_API_KEY` |
| `gemini`     | `GEMINI_API_KEY` |
| `groq`       | `GROQ_API_KEY` |
| `azure`      | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |
| `bedrock`    | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| `vertexai`   | `GOOGLE_API_KEY`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION` |
| `dify`       | `DIFY_API_KEY`, `DIFY_URL` |
| `custom`     | `CUSTOM_LLM_API_KEY`, `CUSTOM_LLM_BASE_URL` |

Fill Agora credentials via the CLI or by hand:

```bash
agora login
agora project use <your-project>
agora project env write server/.env.local   # writes App ID + Certificate
# then optionally add LLM_VENDOR=anthropic + ANTHROPIC_API_KEY=... to server/.env.local
```

> Do **not** add `PORT` to `server/.env.example` — see [07_gotchas](07_gotchas.md).

## Run

```bash
bun run dev              # backend (:8000) + web (:3000) via concurrently
```

Open <http://localhost:3000> → pick an LLM from the dropdown → **Start Conversation** → speak. Backend API docs at <http://localhost:8000/docs>.

## Quick commands

```bash
bun run doctor           # shared prereqs (bun + node_modules); no creds needed
bun run doctor:local     # + .env.local + AGORA_APP_ID/CERTIFICATE present
bun run verify           # web-only gate (doctor + api contracts + web build)
bun run verify:local     # full local gate: backend compile + fastapi smoke + proxy + web build
bun run clean            # remove venvs and build artifacts
```

Backend unit tests run standalone (no cloud, no creds):

```bash
cd server && pytest tests -v
```

## Related Deep Dives

- None. For what each verify command asserts, see [05_workflows](05_workflows.md) and [06_interfaces](06_interfaces.md).
