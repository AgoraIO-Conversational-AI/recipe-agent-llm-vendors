# Agent Development Guide

For coding agents working in `recipe-agent-llm-vendors`. This repository is the
**LLM vendors** recipe in the Agora Conversational AI recipes family: the LLM leg
is a per-vendor switchboard (one readable `build_<vendor>` per vendor) selected via `LLM_VENDOR`.

## How to Load

This repository uses progressive disclosure documentation. Docs live under
`docs/ai/` in three levels.

1. Read [docs/ai/L0_repo_card.md](docs/ai/L0_repo_card.md) to identify the repo.
2. This repo declares `Recipe Role: base`; read [docs/ai/RECIPE.md](docs/ai/RECIPE.md) before changing reusable recipe contracts.
3. Load ALL 8 files in [docs/ai/L1/](docs/ai/L1/). They are small — load all upfront.
4. Follow L2 deep-dive links only when L1 isn't detailed enough. The index is at [docs/ai/L1/L2/_index.md](docs/ai/L1/L2/_index.md).

The sections below remain the canonical contributor handbook for hands-on work;
the `docs/ai/` tree is the structured summary used by AI agents.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. The LLM leg is built from the
  per-vendor builder registry in `server/src/vendors.py`; default vendor `openai` is
  Agora-managed (keyless). SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000): the
  `EventTimeline` and the annotated transcript.
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- No `llm/` service — on the default `openai` vendor the LLM is Agora-managed
  (zero-key by default).

## Pipeline

`DeepgramSTT(nova-3, en)` → `<LLM_VENDOR>` (default `openai`, Agora-managed, keyless) → `MiniMaxTTS`

## Vendor registry

- `server/src/vendors.py` holds `CATEGORY = "LLM"`, the `REGISTRY` table (all nine
  A4.1 LLM vendors), and `build_vendor()` / `required_env()` / `available()` / `needs_key()`.
- `agent.py` reads `LLM_VENDOR` in `__init__` (no validation) and calls
  `build_vendor(self.vendor)` for the LLM leg **in `start()`** — BYO credential
  validation happens there, so `/get_config` stays key-less.
- Only the LLM leg is swapped; STT (`DeepgramSTT`) and TTS (`MiniMaxTTS`) stay on
  the proven keyless configs.

## Event flags (backend)

The agent is started with:
- `audio_scenario = "chorus"` — web client → ultra-low-latency chorus profile
- `data_channel = "rtm"` — routes all events over RTM
- `enable_metrics = True` — per-stage latency metrics
- `enable_error_message = True` — agent + message errors
- `advanced_features = {"enable_rtm": True}`

The web client uses `AgoraVoiceAI` to subscribe and surfaces events as
`TimelineEvent` objects in `EventTimeline`.

## Routing / ownership

- UI, RTC/RTM lifecycle, EventTimeline, and annotated transcript live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- `EventTimeline` type (`TimelineEvent`) is exported from
  `web/src/components/EventTimeline.tsx`; import from there.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000) and `web` (:3000).
  The web app calls `/api/*`; Next rewrites to
  `AGENT_BACKEND_URL=http://localhost:8000`.
- **Deploy:** deploy `web` (Next) + `server` (reachable FastAPI).
  Set `AGENT_BACKEND_URL` in the web deployment.

## Env vars

| Variable | Default | Notes |
|---|---|---|
| `AGORA_APP_ID` | — | required |
| `AGORA_APP_CERTIFICATE` | — | required |
| `LLM_VENDOR` | `openai` | which LLM vendor to build (see README Vendors table) |
| `LLM_MODEL` | per-vendor | optional model override for the selected vendor |
| _vendor creds_ | — | required only for the selected BYO vendor (`required_env(LLM_VENDOR)`) |

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- Add or change LLM vendors only in the `REGISTRY` table in `vendors.py`; the
  framework (`build_vendor`/`required_env`/`available`/`needs_key`) is shared across the
  sibling vendor recipes — keep it identical.
- Validate vendor creds in `start()` via `build_vendor`, never in `__init__`.
- Import `TimelineEvent` from `EventTimeline.tsx`, not from a separate types file.

## Anti-patterns

- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not hardcode a single LLM vendor in `agent.py`; build it via `build_vendor`.
- Do not validate vendor credentials in `__init__` (it would break key-less
  `/get_config` and the managed docker smoke).
- Do not reintroduce `SOURCE_LANG` / `TARGET_LANG` / `TTS_VOICE` — those belong
  to the translator recipe.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or narrower
   `verify:local:fastapi` / `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README,
   the relevant module README, and `server/.env.example` together.
5. If the change touches workflows, interfaces, gotchas, or security details,
   update the matching file under [docs/ai/L1/](docs/ai/L1/) and bump
   `Last Reviewed` in [docs/ai/L0_repo_card.md](docs/ai/L0_repo_card.md).

## Git Conventions

### Commit messages — conventional commits

- **Format:** `type: description` or `type(scope): description`
- **Types:** `feat:` (new feature), `fix:` (bug fix), `chore:` (maintenance, version bumps), `test:` (test additions/changes), `docs:` (documentation)
- **Scoped variant:** `feat(scope):`, `fix(scope):` — e.g. `fix(server): validate vendor creds`
- **Lowercase after prefix** — `feat: add feature`, not `feat: Add feature`
- **Present tense** — "add feature", not "added feature"

### Branch names

- **Format:** `type/short-description` — lowercase, hyphen-separated
- **Types match commit types:** `feat/`, `fix/`, `chore/`, `test/`, `docs/`
- **Examples:** `feat/add-vendor-dify`, `fix/vendor-cred-error`, `docs/progressive-disclosure`

### General rules

- **Repo-local `AGENTS.md` is the authoritative source for repo conventions.**
- **No AI tool names** — never mention claude, cursor, copilot, cody, aider, gemini, codex, chatgpt, or gpt-3/4 in commit messages or PR descriptions.
- **No Co-Authored-By trailers** — omit AI attribution lines.
- **No `--no-verify`** — let git hooks run normally.
- **No git config changes** — do not modify `user.name` or `user.email`.

## Doc Commands

| Command       | When to use                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| generate docs | No `docs/ai/` directory exists yet                                           |
| update docs   | Code changed since the `Last Reviewed` date in L0                            |
| test docs     | Verify docs give agents the right context (writes `docs/ai/test-results.md`) |
| fix docs      | Close findings from a docs review or test run                                |

See the [progressive disclosure standard](https://github.com/AgoraIO-Community/ai-devkit/blob/main/docs/standard/progressive-disclosure-standard.md) and [workflows](https://github.com/AgoraIO-Community/ai-devkit/blob/main/docs/workflows/progressive-disclosure-docs.md) for the full specification.
