# Doc Test Results

**Repo:** `AgoraIO-Conversational-AI/recipe-agent-llm-vendors`
**Branch:** `docs/progressive-disclosure`
**Date:** 2026-06-25
**Tester:** progressive disclosure workflow

---

## Structural Checks

| Check | Result |
| ----- | ------ |
| L0_repo_card.md present | PASS |
| RECIPE.md present | PASS |
| All 8 L1 files present (01–08) | PASS |
| L1/L2/_index.md present | PASS |
| L1/L2/vendor_registry.md present | PASS |
| L1/L2/session_lifecycle.md present | PASS |
| AGENTS.md has `## How to Load` section | PASS |
| AGENTS.md has `## Git Conventions` section | PASS |
| AGENTS.md has `## Doc Commands` section | PASS |
| AGENTS.md stale "docs/ai not present" note removed | PASS |
| CLAUDE.md redirects to @AGENTS.md (unchanged) | PASS |
| README.md unchanged | PASS |
| ARCHITECTURE.md unchanged | PASS |

**Structural checks: 13/13 PASS**

---

## Relative Link Check

Checked all `.md` files under `docs/ai/` (13 files, 35 relative links).

| Result | Count |
| ------ | ----- |
| Broken links | 0 |
| Total relative links | 35 |
| Total files checked | 13 |

**Link check: PASS**

---

## Backend pytest

Venv: `/tmp/v_llm_vendors` (Python 3.14.4, throwaway; deleted after run).
Install: `pip install -r server/requirements.txt -r server/requirements-dev.txt`

```
platform darwin -- Python 3.14.4, pytest-9.1.1
collected 4 items

tests/test_agent_config.py::test_agent_constructs                               PASS
tests/test_agent_construction.py::test_start_constructs_real_agent_and_returns_shape  PASS
tests/test_vendors.py::test_every_vendor_constructs_and_emits_config            PASS
tests/test_vendors.py::test_byo_vendor_missing_creds_raises                     PASS

4 passed in 0.60s
```

**pytest: 4/4 PASS**

---

## Backend compile check

```
python3 -m py_compile server/src/server.py server/src/agent.py server/src/vendors.py
```

**Result: PASS**

---

## Q&A Verification (12 questions across 5 categories)

Each answer verified against source code or docs before marking Pass.

### Category 1 — Setup & Zero-key default

**Q1.** What credentials are required to run the recipe out of the box (default `openai` vendor)?

> **A:** Only `AGORA_APP_ID` and `AGORA_APP_CERTIFICATE`. No LLM API key is required.
>
> **Source:** `server/.env.example`, `server/src/agent.py` (`Agent.__init__` raises only for missing Agora creds), `REGISTRY["openai"] = (build_openai, [])` in `vendors.py`.
> **Status: PASS**

**Q2.** Which command installs all dependencies?

> **A:** `bun run setup` (runs `setup:env`, `setup:server` creating a Python venv, and `setup:web`).
>
> **Source:** `package.json` `setup` script.
> **Status: PASS**

---

### Category 2 — Vendor Registry

**Q3.** How do you add a new LLM vendor to this recipe?

> **A:** Add a `build_<vendor>(env)` function in `server/src/vendors.py` importing the SDK class, add a `REGISTRY` entry `"<name>": (build_<vendor>, ["REQUIRED_ENV_VAR", ...])`, and add the env vars block to `server/.env.example`.
>
> **Source:** `vendors.py` REGISTRY pattern, `docs/ai/L1/05_workflows.md`, `docs/ai/L1/L2/vendor_registry.md`.
> **Status: PASS**

**Q4.** Which vendor is Agora-managed and requires no API key?

> **A:** `openai` — `REGISTRY["openai"] = (build_openai, [])` (empty creds list).
>
> **Source:** `vendors.py` line `"openai": (build_openai, [])`.
> **Status: PASS**

**Q5.** What does `build_vendor("anthropic", {})` raise?

> **A:** `ValueError: LLM vendor 'anthropic' requires environment variable(s): ANTHROPIC_API_KEY`.
>
> **Source:** `vendors.py` `build_vendor()` — checks missing creds and raises `ValueError` naming them. Verified by `test_byo_vendor_missing_creds_raises`.
> **Status: PASS**

**Q6.** What env var overrides the model for any vendor?

> **A:** `LLM_MODEL` — `_model(env, default)` in `vendors.py` returns `env.get("LLM_MODEL") or default`.
>
> **Source:** `vendors.py` `_model()` function, `server/.env.example`.
> **Status: PASS**

---

### Category 3 — Architecture & Boundaries

**Q7.** Why are BYO vendor credentials NOT validated in `Agent.__init__()`?

> **A:** So that `GET /get_config` and the managed Docker smoke test remain key-less even when a BYO `LLM_VENDOR` is configured. Credentials are validated in `start()` via `build_vendor()`.
>
> **Source:** `agent.py` docstring, `ARCHITECTURE.md` "Why creds are validated in start()", `docs/ai/L1/07_gotchas.md`.
> **Status: PASS**

**Q8.** What is the full pipeline for a conversation turn?

> **A:** `DeepgramSTT(nova-3, en)` → `<LLM_VENDOR>` (default `openai`, Agora-managed) → `MiniMaxTTS(speech_2_6_turbo)`.
>
> **Source:** `agent.py` `start()`, `README.md` Pipeline section, `ARCHITECTURE.md`.
> **Status: PASS**

---

### Category 4 — Interfaces & Routes

**Q9.** Which browser-facing route populates the in-UI vendor dropdown?

> **A:** `GET /api/vendors` — rewrites to `/vendors` on the backend; returns `{ default, vendors[{ name, needs_key, required_env }] }`.
>
> **Source:** `server.py` `list_vendors()`, `web/next.config.ts` rewrites, `web/src/services/api.ts` `getVendors()`.
> **Status: PASS**

**Q10.** What does `POST /api/startAgent` return in the `data` field?

> **A:** `{ agent_id, channel_name, vendor (selected vendor name), status: "started" }`.
>
> **Source:** `agent.py` `start()` return dict, `server.py` `start_agent()` response.
> **Status: PASS**

---

### Category 5 — EventTimeline & RTM

**Q11.** Where must the `TimelineEvent` type be imported from?

> **A:** `web/src/components/EventTimeline.tsx` — it is exported there; do not import from a separate types file.
>
> **Source:** `EventTimeline.tsx` line `export type TimelineEvent = ...`, `AGENTS.md` Patterns section.
> **Status: PASS**

**Q12.** What are the four `TimelineEvent.kind` values and their source RTM events?

> **A:** `state` (from `AGENT_STATE_CHANGED`), `metric` (from `AGENT_METRICS`), `error` (from `AGENT_ERROR` or `MESSAGE_ERROR`), `turn` (from `TRANSCRIPT_UPDATED`).
>
> **Source:** `EventTimeline.tsx` `KIND_STYLES`, `ARCHITECTURE.md` Event surface table.
> **Status: PASS**

---

## Summary Table

| Category | Questions | Pass | Fail |
| -------- | --------- | ---- | ---- |
| Setup & Zero-key default | 2 | 2 | 0 |
| Vendor Registry | 4 | 4 | 0 |
| Architecture & Boundaries | 2 | 2 | 0 |
| Interfaces & Routes | 2 | 2 | 0 |
| EventTimeline & RTM | 2 | 2 | 0 |
| **Total** | **12** | **12** | **0** |

---

## Fix / Retest

No failures. No fixes required.

---

## Overall Result

**PASS** — 13/13 structural checks, 0 broken links (35 checked), 4/4 pytest, 12/12 Q&A.
