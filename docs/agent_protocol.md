# Desktop Agent → API Protocol (Phase 1)

Purpose: allow the desktop agent to capture activity (apps, calendar, IDE, files), detect idle, group context, and send suggested time entries reliably to backend.

## Agent Architecture (local)
- Collectors: OS/app usage (active window/app name), calendar reader (Google/Outlook via API), IDE plugin signals, file edits.
- Sampler: polls active app/window every N seconds; records spans with start/end, title, path, tags.
- Idle detector: watches input events; marks idle spans; splits sessions on idle > threshold.
- Grouper: merges contiguous spans with similar context (app + project hints) into candidate blocks.
- Queue: local persistent queue (disk) for events to send; stores retry state.
- Auth: device login via browser SSO → agent-specific refresh token; tokens stored in OS keychain.

## Event Schema (agent → API)

`activity_event` (batched):
- event_id: uuid (client-generated)
- device_id: stable uuid per install
- user_id: optional (if known), else inferred from token
- captured_at: ISO8601 timestamptz (when recorded)
- started_at, ended_at: ISO8601
- source: app|calendar|ide|file|manual
- app_name: text (e.g., VS Code, Chrome)
- window_title: text (sanitized)
- file_path: text (optional; hash or short path if sensitive)
- project_hint: text (repo name, calendar event title, client tag)
- tags: array<text>
- idle: boolean
- duration_ms: int
- metadata: object (key-value, e.g., meeting attendees, branch name)

`time_suggestion` (API → agent optional pull):
- suggestion_id: uuid
- project_id: uuid
- started_at, ended_at
- description
- confidence: 0-1
- source_events: array<event_id>
- status: pending|accepted|rejected

## API Surface (ingest-first)
- POST /agent/v1/events/batch
  - Body: { device_id, events: [activity_event], cursor? }
  - Response: { accepted: [event_id], rejected: [{event_id, reason}], next_cursor }
  - Idempotency: Idempotency-Key header to dedupe; server stores recent keys for 24h.
- POST /agent/v1/suggestions/:id/decision
  - Body: { status: accepted|rejected, replaced_by_time_entry_id? }
- POST /agent/v1/health
  - Body: { device_id, agent_version, platform, last_sync_at, queue_depth }

## Transport & Reliability
- Auth: Authorization: Bearer <access>; refresh via /auth/refresh. Agent requests limited scope token.
- Batch size: default 100 events; compress with gzip.
- Retries: exponential backoff with jitter; stop retry after 7 days per event.
- Clock skew: agent includes captured_at; server trusts started/ended if within allowed skew (e.g., ±5m); otherwise normalizes.
- Offline mode: queue persists to disk; flushes when online; respect rate limits (429) with backoff.

## Server Processing Pipeline
1) Ingest API validates signature, required fields, and timestamp skew.
2) Writes raw events to activity_events table (or log store) with device_id, user_id, jsonb payload.
3) Normalizer: dedup by event_id + device_id; strips PII if configured; enriches with client/project hints.
4) Grouper: groups events by temporal proximity and context to form suggested time blocks.
5) Rule application: maps blocks to projects using heuristics (calendar titles, repo names, previous decisions).
6) Emits `time_suggestions` for user approval; marks derived `suggestion_id` linking back to source events.

## Idle & Context Grouping (MVP)
- Idle threshold: 5 minutes default; splits a block when idle detected.
- Merge rule: same app_name + similar window_title prefix within 10-minute gap.
- Calendar overlay: meeting events create candidate project_hint and descriptions.
- IDE hints: repo name → project mapping table; branch name stored in metadata.

## Security & Privacy
- Avoid sending full file paths if user opts out; allow hashing path.
- Strip window titles containing URLs/domains if privacy setting enabled.
- Enforce TLS; sign downloads of agent updates; pin API host.

## Observability
- Metrics: ingest_success, ingest_failure_reason, queue_flush_latency, dedup_count, suggestions_created.
- Logs: per batch outcome; store correlation id (request id) for tracing.

## Open Questions
- Should the agent perform local suggestion generation to reduce server load? (MVP: server-side.)
- Do we support mobile capture later? (Define separate source type.)
- Version gating: minimum agent version allowed by server?
