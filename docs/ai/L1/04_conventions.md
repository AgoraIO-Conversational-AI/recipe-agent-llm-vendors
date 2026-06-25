# 04 · Conventions

> Coding patterns shared across `server/` and `web/`. Follow these to keep local and deployed modes aligned and the vendor registry consistent.

## Boundary ownership

- Browser code calls only `/api/*`. Backend placement is hidden behind Next rewrites (`web/next.config.ts`).
- **Never** add `web/app/api/**/route.ts` for agent/token logic — `verify-api-contracts.ts` fails the build if a `route.ts` appears under `app/api`.
- Token generation and the App Certificate stay in `server/`.

## Vendor registry rules

- All LLM vendor logic lives in `server/src/vendors.py` (`REGISTRY` + one `build_<vendor>` per vendor).
- `agent.py` always calls `build_vendor(self.vendor)` to obtain the LLM — never hard-codes a vendor class.
- Do not validate BYO vendor credentials in `Agent.__init__()` — credentials are checked in `start()` via `build_vendor()` so `/get_config` stays key-less.
- To add a vendor: add a `build_<vendor>(env)` function + a `REGISTRY` entry. The framework (`build_vendor` / `required_env` / `available` / `needs_key`) is shared across sibling recipes — keep it identical.
- `needs_key(name)` returns `True` if the vendor's `required_env` list is non-empty.

## Backend (Python / FastAPI)

- Async throughout: route handlers are `async def`; the agent uses `AsyncAgora` and `create_async_session`.
- Request bodies are Pydantic models (`StartAgentRequest`, `StopAgentRequest`). Field names are **camelCase** (`channelName`, `rtcUid`, `userUid`, `vendor`, `agentId`) to match the browser client.
- Error mapping is centralized: `_to_http_error()` maps `ValueError → 400`, `RuntimeError → 500`, else 500. Raise plain `ValueError`/`RuntimeError`; let the route convert.
- Logging via `logging.getLogger("uvicorn.error")`.
- Env read with `os.getenv`; `.env.local` then `.env` loaded with `override=True`.

## Response envelope

All backend JSON responses use:

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` is present only when the route returns a payload. The browser client treats `code !== 0` (or missing `data`) as an error.

## Pipeline configuration

- `DeepgramSTT(model="nova-3", language="en")` and `MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")` are fixed; only the LLM leg changes.
- Turn detection (`speech_threshold`, `start_of_speech`, `end_of_speech`) is configured on `AgoraAgent(...)` directly (not on the LLM vendor).
- Session flags: `audio_scenario="chorus"`, `data_channel="rtm"`, `enable_error_message=True`, `enable_metrics=True`, `advanced_features={"enable_rtm": True}`.

## Web (TypeScript / Next.js)

- Lint/format with Biome (`bun run lint`, `bun run lint:fix` in `web/`).
- RTC client creation must be StrictMode-safe (strict mode is on).
- `TimelineEvent` type is exported from `web/src/components/EventTimeline.tsx`; import from there.
- API client lives in `src/services/api.ts`; UI never calls `fetch` to the backend directly.
- `normalizeTranscript` maps `uid === '0'` to the local UID; preserve this for correct speaker mapping.

## Testing approach

- Backend: `pytest` in `server/`, standalone — `conftest.py` fakes env, so no cloud or real creds are needed.
- Web: contract/proxy/fastapi smoke scripts under `web/scripts/` run without live Agora calls.
- Run the **narrowest** relevant verify command before finishing (see [05_workflows](05_workflows.md)).

## Doc upkeep

When you change request/response contracts, env vars, vendor registry, or workflow, update the web client, backend, contract checks, README, **and** the matching `docs/ai/L1/` file together, then bump `Last Reviewed` in [L0](../L0_repo_card.md).

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — registry design, per-vendor SDK fields, and adding a vendor.
