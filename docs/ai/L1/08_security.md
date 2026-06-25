# 08 · Security

> Trust boundaries, secret handling, and auth for the LLM vendors recipe.

## Trust boundaries

| Hop                           | Auth                                                                                    |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| Browser → agent backend       | None in local dev (the `/api/*` rewrite is same-origin).                                |
| Agent backend → Agora cloud   | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.                      |
| Agora cloud → LLM (managed)   | Agora-managed key for the default `openai` vendor — transparent to this recipe.         |
| Agora cloud → LLM (BYO)       | Your vendor key (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, etc.) passed in the vendor config. |

## Secret handling

- **Server-only secrets:** `AGORA_APP_CERTIFICATE` and all BYO vendor API keys live only in `server/.env.local` and never reach the browser.
- The browser receives only a short-lived Agora token; it never sees the App Certificate or any LLM key.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholder comments only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.__init__()` rejects missing `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE`.
- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- `build_vendor()` rejects a BYO vendor with missing credentials (400) before any Agora call.
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; exceptions map to 400/500 without leaking internals to the client beyond the message.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- BYO vendor API keys (`ANTHROPIC_API_KEY`, etc.) are passed as constructor arguments in the vendor config at session start. They are never returned to the browser.
- The published Docker image is **backend-only** (`:8000`); it does not bundle secrets.

## Related Deep Dives

- None.
