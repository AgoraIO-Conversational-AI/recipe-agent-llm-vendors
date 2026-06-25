# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the vendor registry API.

## Backend routes (port 8000)

The browser calls these as `/api/<name>`; Next rewrites to the backend `/<name>`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.
- Always works key-less regardless of `LLM_VENDOR`.

### `GET /vendors`

- No query params.
- Returns `data`: `{ default: string, vendors: [{ name, needs_key, required_env[] }] }`.
- `default` is the current `LLM_VENDOR` env value (defaults to `"openai"`).
- Used by the in-UI dropdown to populate vendor choices.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, vendor?: string, parameters?: object }`.
  - `vendor`: if present, overrides `LLM_VENDOR` for this session.
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, vendor (selected), status: "started" }`.
- 400 if BYO vendor credentials are missing, or `channelName`/`rtcUid`/`userUid` invalid.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path         | Backend destination  |
| -------------------- | -------------------- |
| `/api/get_config`    | `/get_config`        |
| `/api/startAgent`    | `/startAgent`        |
| `/api/stopAgent`     | `/stopAgent`         |
| `/api/vendors`       | `/vendors`           |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `getVendors() → { default: string; vendors: VendorOption[] }`
- `startAgent(channelName, rtcUid, userUid, vendor?) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope              | Required | Default                 |
| ----------------------- | ------------------ | :------: | ----------------------- |
| `AGORA_APP_ID`          | backend            |    ✅    | —                       |
| `AGORA_APP_CERTIFICATE` | backend            |    ✅    | —                       |
| `LLM_VENDOR`            | backend            |          | `openai` (keyless)      |
| `LLM_MODEL`             | backend            |          | per-vendor default      |
| `AGENT_GREETING`        | backend            |          | built-in line           |
| _vendor creds_          | backend            |  BYO ✅  | — (see below)           |
| `AGENT_BACKEND_URL`     | web (deploy)       |    ✅\*  | `http://localhost:8000` (dev) |
| `PORT`                  | backend (env only) |          | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

### BYO vendor required env vars

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

## Vendor registry API (`server/src/vendors.py`)

- `build_vendor(name, env=os.environ) → SDK vendor object` — constructs the vendor; raises `ValueError` listing missing env vars.
- `required_env(name) → List[str]` — credential env vars for the named vendor.
- `available() → List[str]` — sorted list of registered vendor names.
- `needs_key(name) → bool` — `True` if the vendor requires at least one credential.

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — every vendor's SDK fields and the full registry design.
