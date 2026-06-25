# Deep Dive — Session Lifecycle

**When to Read This:** You are touching the browser-side join/start/stop flow, the vendor dropdown, the RTM event subscription, or the EventTimeline wiring. For the high-level topology, start at [02_architecture](../02_architecture.md).

## Browser orchestration — overview

```
LandingPage mounts
  │
  ├── getConfig()           GET /api/get_config  → { app_id, token, uid, channel_name, agent_uid }
  ├── getVendors()          GET /api/vendors      → { default, vendors[] }
  │                         (populates the pre-call vendor dropdown)
  │
  │  user selects vendor + presses Start
  │
  ├── RTC join (via AgoraProvider / ConversationComponent)
  ├── RTM login (via RTMClient)
  ├── startAgent(channel, rtcUid, userUid, vendor?)
  │        POST /api/startAgent → { agent_id, channel_name, vendor, status }
  │
  │  conversation is live
  │  RTM events arrive → ConversationComponent appends TimelineEvent
  │
  └── stopAgent(agentId)    POST /api/stopAgent
      RTC leave + RTM logout (teardown in LandingPage)
```

## Vendor selection flow

1. `LandingPage` calls `getVendors()` on mount to populate `QuickstartPreCallCard`'s dropdown.
2. Each `VendorOption` carries `{ name, needs_key, required_env[] }` so the UI can label "needs key" vendors.
3. The selected vendor name is passed as the `vendor` field to `startAgent()`.
4. If `vendor` is omitted or `null`, the backend falls back to `LLM_VENDOR` env.

## RTC / RTM lifecycle

- `AgoraProvider` and `ConversationComponent` own RTC (audio stream) and RTM (event bus).
- RTM login waits up to 600ms for a `CONNECTED` status event (`waitForRtmConnected`).
- `DEFAULT_AGENT_UID = 123456` is exported from `web/src/lib/agora.ts`; passed as the initial pre-call estimate when the actual `agent_uid` from `get_config` is not yet available.

## RTM event → TimelineEvent mapping

`ConversationComponent` subscribes to RTM events via `AgoraVoiceAI` (from `agora-agent-client-toolkit`). Each event is mapped to a `TimelineEvent` and appended to a buffer capped at 50:

| SDK event              | `TimelineEvent.kind` | Key payload                                         |
| ---------------------- | -------------------- | --------------------------------------------------- |
| `AGENT_STATE_CHANGED`  | `state`              | `listening`, `thinking`, `speaking`, `idle`         |
| `AGENT_METRICS`        | `metric`             | Stage type, metric name, value (ms)                 |
| `AGENT_ERROR`          | `error`              | Error type + message                                |
| `MESSAGE_ERROR`        | `error`              | RTM message error code + message                    |
| `TRANSCRIPT_UPDATED`   | `turn`               | Role (agent/user) + text snippet                    |

`TimelineEvent` is exported from `web/src/components/EventTimeline.tsx`. Import it from there, not a separate types file.

## `EventTimeline` rendering

`EventTimeline` receives `events: TimelineEvent[]` and renders them in reverse-chronological order (`.reverse()`). Each event shows a colored badge by kind (`state`=blue, `metric`=green, `error`=red, `turn`=violet) and a formatted timestamp.

## Transcript normalization

`normalizeTranscript` (in `web/src/lib/conversation.ts`) maps `uid === '0'` to the local UID. Preserve this mapping — the agent SDK sometimes emits `uid: "0"` for the local user, and speaker attribution depends on a concrete UID.

`normalizeTranscriptSpacing` adds spaces after sentence-ending punctuation and before capital letters to clean up concatenated transcript fragments.

## Token renewal

Token expiry is 3600s per `get_config` call. If you add a long-running session scenario, you will need to call `getConfig` again to renew the Agora token before the session expires.

## Stop flow

`stopAgent(agentId)` sends `POST /api/stopAgent`. The backend first tries `session.stop()` on the active in-memory session, then falls back to `client.stop_agent(agent_id)` via the stateless client path. After `stopAgent` resolves, `LandingPage` triggers RTC leave and RTM logout.

## Related L1

- [02_architecture](../02_architecture.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
