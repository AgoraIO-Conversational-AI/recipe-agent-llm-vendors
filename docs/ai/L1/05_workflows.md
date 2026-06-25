# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Add a new LLM vendor

1. In `server/src/vendors.py`: add a `build_<vendor>(env)` function that constructs the SDK vendor class with all required fields.
2. Add a `REGISTRY` entry: `"<name>": (build_<vendor>, ["REQUIRED_ENV_VAR", ...])`. Empty list = keyless.
3. Add the vendor's env vars block (commented out) to `server/.env.example`.
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Change an existing vendor's config or model

1. Edit the `build_<vendor>(env)` function in `server/src/vendors.py`.
2. If defaults change, update `_model(env, "<new_default>")` in the builder.
3. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Change the agent greeting

1. Set `AGENT_GREETING` in `server/.env.local`, or edit the default in `server/src/agent.py`.
2. Verify: `bun run verify:backend`.

## Change STT or TTS config

1. Edit the `DeepgramSTT(...)` or `MiniMaxTTS(...)` constructor in `Agent.start()` (`server/src/agent.py`).
2. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Change turn detection parameters

1. Edit the `turn_detection` dict passed to `AgoraAgent(...)` in `Agent.start()` (`server/src/agent.py`). See [07_gotchas](07_gotchas.md) for the correct placement.
2. Verify: `bun run verify:local:fastapi`.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Run / debug locally

```bash
bun run dev              # both processes
bun run doctor:local     # check creds + .env.local before a live call
```

## Switch LLM vendor at runtime

- Pick from the **dropdown** on the pre-call screen (calls `GET /api/vendors` + passes `vendor` to `POST /api/startAgent`). No backend restart needed.
- Or set `LLM_VENDOR=<name>` in `server/.env.local` and restart.

## Verify before finishing

| Change touches…              | Run                                                                   |
| ---------------------------- | --------------------------------------------------------------------- |
| Vendor registry / agent      | `bun run verify:backend` + `cd server && pytest tests -v`             |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`      |
| Web only                     | `bun run verify:web`                                                  |
| Anything end-to-end (local)  | `bun run verify:local`                                                |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` (or any reachable FastAPI host); the published backend-only image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-llm-vendors` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.
4. Set `LLM_VENDOR` + that vendor's credentials in the server environment if not using the default `openai`.

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — full vendor build details and SDK fields.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/renewal/teardown and EventTimeline wiring.
