# Mobius MCP Setup Guide

Full multi-client configuration reference for the Mobius MCP server.
This is the standalone document — the SKILL.md has a condensed summary.

Last verified: 2026-11-10 (32 tools, OAuth discovery live).

## Connection Details

| Field | Value |
|-------|-------|
| Transport | Streamable HTTP (JSON-RPC over POST) |
| URL | `https://mobius.feedmob.com/api/mcp` |
| Auth (recommended) | OAuth 2.1 — browser sign-in with your Mobius account |
| Auth (fallback) | `Authorization: Bearer mob_...` |
| Session required | No (stateless) |
| Tool count | 32 |
| Server name | `mobius` |

## Choose an auth method

| You are… | Use | Why |
|----------|-----|-----|
| A person using an interactive MCP client (Claude Code, Claude desktop/web, Cursor, VS Code…) | **OAuth** | No token to create, copy, rotate or leak. Actions are signed as you. |
| A headless runtime acting on its own (Hermes gateway, agent-worker, a cron loop) | **Agent pairing** → `mob_` token | Browser sign-in cannot finish headless; a paired agent gets its own identity and an append-only permission set. |
| A script or client with no OAuth support | **Personal token** (`mob_`) | Fallback only. |

## OAuth (recommended)

The server advertises standard MCP OAuth. Any MCP client with OAuth support
discovers it automatically from the `401` response — you only give it the URL.

| Item | Value |
|------|-------|
| Protected-resource metadata | `https://mobius.feedmob.com/.well-known/oauth-protected-resource` |
| Authorization-server metadata | `https://mobius.feedmob.com/.well-known/oauth-authorization-server` |
| Dynamic client registration | `https://mobius.feedmob.com/api/oauth/register` |
| Grant | `authorization_code` + PKCE (`S256`), `refresh_token` |
| Scopes | `mobius:read`, `mobius:write` |

### Claude Code

```bash
claude mcp add --transport http --scope user mobius https://mobius.feedmob.com/api/mcp
```

Then in a Claude Code session: `/mcp` → `mobius` → **Authenticate** → sign in in the
browser → back in `/mcp` it shows connected.

No `claude` CLI (desktop app only)? Add the same entry by hand to the top-level
`mcpServers` object in `~/.claude.json`, then open a **new** session and run `/mcp`:

```json
{
  "mcpServers": {
    "mobius": { "type": "http", "url": "https://mobius.feedmob.com/api/mcp" }
  }
}
```

### Claude (claude.ai web / desktop / mobile)

Settings → Connectors → **Add custom connector** → name `Mobius`, URL
`https://mobius.feedmob.com/api/mcp` → **Connect** → sign in. The connector follows
your claude.ai account across apps.

### Cursor (`mcp.json`) / VS Code / other OAuth-capable clients

```json
{
  "mcpServers": {
    "mobius": { "url": "https://mobius.feedmob.com/api/mcp" }
  }
}
```

No `headers` block — the client opens the browser sign-in on first use.

### Verify

Call the `whoami` tool. Expected: your own `name` / `email`, `kind: "person"`, and a
`capabilities` object. Then `list_teams` should list the workspace's teams.

## Agent pairing (headless runtimes)

A runtime that runs unattended should become a Mobius **agent** with its own
identity instead of borrowing a person's login. The flow is an OAuth-style device
flow: the runtime shows a code, a person approves it in Mobius.

The authoritative, versioned instructions are served by Mobius itself — always
read them instead of copying from here:

- MCP tool: `agent_guide` (optionally `runtime: "hermes"` / `"claude-code"` / …)
- Or without credentials: `GET https://mobius.feedmob.com/api/agents/guide`

Key rules from the guide:
1. Ask the person what to name the agent; never invent a name.
2. Never print the `pollToken` or the resulting `mob_` token.
3. The person decides the agent kind (personal / team / workspace) on the approve page.
4. Agents are **append-only**: no archive, delete, editing others' comments,
   project management, or Mobius AI tools.
5. A 401 after pairing means paused/revoked — stop and tell the owner.

Hermes has a first-party plugin served by Mobius
(`curl -fsSL https://mobius.feedmob.com/api/agents/plugin/hermes | tar -xz -C ~/.hermes/plugins`);
see `agent_guide(runtime="hermes")` for the full recipe.

## Personal token (fallback)

1. Mobius → Settings → API & Tokens → generate a token (starts with `mob_`).
2. Keep it in an env var or the client's secret store — never in git.

### Hermes (`~/.hermes/config.yaml`)

```yaml
mcp_servers:
  mobius:
    url: "https://mobius.feedmob.com/api/mcp"
    headers:
      Authorization: "Bearer mob_YOUR_TOKEN"
    timeout: 180
```

Prefer `url` + `headers` over `npx mcp-remote` + OAuth for headless gateways: an
OAuth server that needs a browser cannot finish inside a gateway's discovery window.

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "mobius": {
      "command": "npx",
      "args": ["mcp-remote", "https://mobius.feedmob.com/api/mcp",
               "--header", "Authorization: Bearer mob_YOUR_TOKEN"]
    }
  }
}
```

(Or skip the token entirely and add a custom connector — see OAuth above.)

### Cline (`cline_mcp_settings.json`)

```json
{
  "mcpServers": {
    "mobius": {
      "url": "https://mobius.feedmob.com/api/mcp",
      "headers": { "Authorization": "Bearer mob_YOUR_TOKEN" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Continue (`config.yaml`)

```yaml
mcpServers:
  - name: mobius
    type: streamable-http
    url: https://mobius.feedmob.com/api/mcp
    requestOptions:
      headers:
        Authorization: "Bearer mob_YOUR_TOKEN"
```

## AI Agent Quick-Setup Prompt

Paste this to any AI agent to have it configure itself:

```
Add the Mobius MCP server to your configuration.

- Transport: Streamable HTTP
- URL: https://mobius.feedmob.com/api/mcp
- Auth: OAuth (the server advertises it via its 401 response). If your client
  supports MCP OAuth, add the URL with no auth header and let me sign in in the
  browser. If you are a headless runtime, call GET
  https://mobius.feedmob.com/api/agents/guide and follow its pairing steps instead.
  Do not ask me to paste a token into chat.

After connecting, call `whoami` and tell me the name, kind and readable teams it
reports, then call `list_teams`.
```

## All 32 MCP Tools

`*` = people only (refused to agent tokens). Unknown arguments are rejected.

### Identity & guide (2)

| Tool | Key Parameters |
|------|----------------|
| `whoami` | — |
| `agent_guide` | `runtime` |

### Read (8)

| Tool | Key Parameters |
|------|----------------|
| `list_issues` | `teamKey`, `stateType`, `stateNames`, `labels`, `assigneeEmail`, `noAssignee`, `query`, `priority`, `priorities`, `projectName`, `createdAfter/Before`, `updatedAfter/Before`, `dueAfter/Before`, `parentIdentifier`, `hasParent`, `hasChildren`, `delegatedToEmail`, `archived`, `sortBy`, `sortOrder`, `limit` (≤200), `cursor` |
| `get_issue` | `identifier` (e.g. `"AI-1234"`) — includes comments, links, attachments, activity |
| `list_teams` | — (keys + workflow states) |
| `list_projects` | — |
| `list_users` | — (name + email) |
| `list_labels` | — |
| `list_attachments` | `identifier` |
| `read_attachment` | `id`, `maxChars` — text types only |

### Write issues (4)

| Tool | Key Parameters |
|------|----------------|
| `create_issue` | `teamKey`*, `title`*, `description`, `priority`, `labels`, `assigneeEmail`, `parentIdentifier` |
| `update_issue` | `identifier`*, `stateName`, `title`, `description`, `priority`, `assigneeEmail`, `delegateToEmail`, `labels` (replaces), `dueDate`, `projectName`, `parentIdentifier` |
| `archive_issue`\* | `identifier` |
| `unarchive_issue`\* | `identifier` |

### Comments (3)

| Tool | Key Parameters |
|------|----------------|
| `add_comment` | `identifier`, `body` |
| `update_comment`\* | `commentId`, `body` |
| `delete_comment`\* | `commentId` |

### Links & attachments (4)

| Tool | Key Parameters |
|------|----------------|
| `add_issue_link` | `identifier`, `url`, `title`, `kind` (`pr` / `commit` / `link`) |
| `remove_issue_link`\* | `id` |
| `upload_attachment` | `filename`, `mimeType`, `dataBase64` or `fileUrl`, `identifier` |
| `delete_attachment`\* | `id` |

### Projects (2)

| Tool | Key Parameters |
|------|----------------|
| `create_project`\* | `name`, `description`, `status`, `leadEmail`, `teamKeys` |
| `update_project`\* | `name`, `status`, `health`, `leadEmail`, `targetDate` |

### Mobius AI (3) — spend Mobius AI credits

| Tool | Key Parameters |
|------|----------------|
| `ask_mobius`\* | `question` |
| `workspace_briefing`\* | — |
| `triage_issue`\* | `identifier`, `apply` |

### Journal (6) — the token owner's own, private notebook

| Tool | Key Parameters |
|------|----------------|
| `journal_read` | `date` or `limit` |
| `journal_append` | `line`, `heading` (`记录` / `待办`), `date` |
| `journal_todos` | `days` |
| `list_journal_topics` | — |
| `journal_entries` | `topicId`, `kinds`, `limit` |
| `journal_entry_append` | `topicId`, `kind`, `body`, `data` |

## Key Concepts

### Priority Levels

`0`=No priority, `1`=Urgent, `2`=High, `3`=Medium, `4`=Low

### State Types

| `stateType` | Typical `stateNames` |
|-------------|---------------------|
| `backlog` | Backlog |
| `unstarted` | Todo |
| `started` | In Progress, In Review |
| `completed` | Done |
| `canceled` | Canceled (and Duplicate on the AI team — query it with `stateNames`) |

### Team Keys

Call `list_teams` for the live list of team keys and their workflow states
(e.g. `AI` for the AI team). Don't hardcode them — teams get added and retired.

## Troubleshooting

- **`/mcp` shows `mobius` needs authentication** — expected on first use; click Authenticate.
- **Browser sign-in opens but the client never connects** — make sure you are signed
  in to mobius.feedmob.com in that browser, then retry Authenticate from the client.
- **401 Unauthorized** — OAuth session expired (re-authenticate in the client), or the
  token was revoked / agent paused. Do not retry in a loop.
- **403 on a write** — permission boundary (team membership or agent kind). Check `whoami`.
- **No tools discovered** — URL must be `/api/mcp` (not `/mcp`). Check network/VPN.
- **Unknown argument error** — Mobius MCP rejects unknown params (doesn't ignore them).
- **Comments show as "Mobius AI"** — you are on the shared token. Switch to OAuth.

## Technical Notes (discovered via live probing)

- `POST /api/mcp` without credentials returns `401` with
  `WWW-Authenticate: Bearer resource_metadata="https://mobius.feedmob.com/.well-known/oauth-protected-resource"`.
- `GET /api/mcp` returns 405 with hint: "send JSON-RPC via POST".
- No `Mcp-Session-Id` header returned or required — fully stateless.
- `GET /api/mcp/events?wait=25&cursor=<id>` is the agent event feed (bot tokens only;
  403 for a person). Never poll it by hand while a plugin/worker drains it.
