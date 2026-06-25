# 07 · Gotchas

> Non-obvious pitfalls specific to the LLM vendors recipe. Read before changing the agent, vendor registry, env, or verify scripts.

## BYO vendor credentials are validated at agent start, not boot

The server boots and `/get_config` works **without any LLM API key** (so `doctor`/contract checks work). `POST /startAgent` returns **400** if a BYO vendor is selected and its credentials are missing — `build_vendor()` raises `ValueError` naming the missing vars. `Agent.__init__` raises only for missing `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE`. Don't move the vendor credential check into `__init__`.

## Turn detection is on `AgoraAgent`, not on the LLM vendor

Unlike the realtime recipe (where VAD is MLLM-owned), the cascading pipeline here sets `turn_detection` as a kwarg directly on `AgoraAgent(...)`. The LLM vendor objects (`OpenAI`, `Anthropic`, etc.) do not own turn detection. Do not add a VAD config to the vendor builder functions.

## `vendor` field in `startAgent` overrides `LLM_VENDOR`

`POST /startAgent` accepts an optional `vendor` field. When provided, it overrides the server-side `LLM_VENDOR` env var for that session. The in-UI dropdown uses this path. Omit it to fall back to `LLM_VENDOR`.

## Do not hard-code a vendor in `agent.py`

`agent.py` must always call `build_vendor(selected)`. Do not import or instantiate a vendor class directly in `agent.py` — that breaks the registry pattern and makes vendor tests useless.

## `REGISTRY` framework is shared across sibling recipes

The `build_vendor` / `required_env` / `available` / `needs_key` framework in `vendors.py` is identical across the sibling vendor recipes (LLM, STT, TTS). Only `CATEGORY` and `SPECS`/`REGISTRY` differ. Keep the framework code identical; do not diverge it.

## `TimelineEvent` must be imported from `EventTimeline.tsx`

The `TimelineEvent` type is exported from `web/src/components/EventTimeline.tsx`. Do not move it to a separate types file — the component and the type are co-located intentionally.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` and loads env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobble the injected port and break the smoke test.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid`, `vendor` (camelCase) to match the browser client. `StopAgentRequest` uses `agentId`. Renaming one side without the other breaks the contract tests.

## `startAgent` returns `vendor` in the response

`Agent.start()` returns `{ agent_id, channel_name, vendor, status }`. The `vendor` field confirms which vendor was actually used (the per-request override or `LLM_VENDOR`). Do not drop it.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `socksio` (in `requirements.txt`) plus `all_proxy` to route the backend through SOCKS.

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — correct vendor build wiring.
