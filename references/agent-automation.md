# Mobius Agent & Automation Endpoints

Discovered while exploring Mobius for AI-1234. These endpoints are NOT in the
main API table and are easy to trigger by accident.

## Endpoints

### `GET /api/agents` — list configured agents

Returns the workspace's AI agents. Both are bots (`isBot: true`).

```json
[
  {"id":"<id>","name":"Mobius Agent",
   "email":"<agent email>","title":"Agent (Beta)","online":true,
   "liveTokenCount":1,"tokenPrefix":"mob_…"},
  {"id":"<id>","name":"<second agent>",
   "email":"<agent email>","title":"Agent (Beta)","online":false,
   "tokenPrefix":"mob_…"}
]
```

- `Mobius Agent` is the triage/automation bot (online, active).
- `<second agent>` is a second agent (often offline).
- Sub-routes like `/api/agents/{id}` and `/api/agents/{id}/issues` return 404
  (Next.js catch-all) — only the bare `/api/agents` list works.

### `GET /api/settings` — agent model & integration config

```json
{
  "provider": "openai",
  "effectiveBaseUrl": "https://<internal model proxy>/v1",
  "effectiveModel": "<model>",
  "apiKeySet": true,
  "enabled": true,
  "autoTriage": false,
  "slackWebhookUrl": "",
  "slackConfigured": false,
  "defaults": {"baseUrl":"https://api.anthropic.com","model":"claude-opus-4-8"},
  "models": [{"id":"claude-opus-4-8",...}, ...]
}
```

- Underlying model is **<model>** via a workspace-hosted model proxy
  (`<internal model proxy>/v1`), NOT raw OpenAI/Anthropic.
- `enabled: true` = agent is globally active. `autoTriage: false` means the
  agent does NOT triage every issue automatically — it only acts when an issue
  has a `delegatedAgentId` pointing at it (see pitfall in SKILL.md).
- `slackConfigured: false` — no Slack webhook integration is wired.

## delegatedAgentId — the tripwire

Every issue has a `delegatedAgent` field (null by default). Setting it via PATCH
arms the `Mobius Agent` against that issue. Observed side effects:

1. Edits the title (sometimes multiple times — 4 revisions seen on one issue).
2. Rewrites the description with an `<!-- ai-context:start -->` block:
   `AI 背景补全 / 背景 / AI 理解 / 会议证据 / 建议补充 / 待确认`.
3. Changes state (e.g. Todo → In Progress).
4. Adds labels (assignee's personal label).
5. **Auto-creates sub-issues** derived from the description.
6. Posts `description_edited` activity events attributed to `Mobius AI`.

All within ~30 seconds of the PATCH. Unsetting the field (`delegatedAgentId: null`)
stops future triage but the artifacts persist — clean up manually:

```bash
# Remove each auto-created sub-issue
curl -X DELETE -H "Authorization: Bearer $MOBIUS_API_KEY" \
  https://mobius.feedmob.com/api/issues/<sub_issue_id>
# Post an explanatory comment on the parent
curl -X POST -H "Authorization: Bearer $MOBIUS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"body":"...explanation..."}' \
  https://mobius.feedmob.com/api/issues/<parent_id>/comments
```

## How Mobius collaboration actually works

There is **no separate `/api/chat` or `/api/conversations` endpoint.** Mobius's
human↔agent collaboration model is: **the issue comment thread IS the chat.**
Agents participate by posting comments (as bot users) and by mutating issue
fields. This contrasts with dedicated chat tools (chat-first tool, Slack) which have
real-time message channels separate from task state.

For the chat-first tool-vs-Mobius agent-collaboration comparison (why chat-first tool is
"native agent" and Mobius is "agent-attached"), see the AI-1234 ticket notes.
