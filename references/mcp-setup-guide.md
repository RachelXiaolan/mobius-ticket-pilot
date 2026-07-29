# Mobius MCP Setup Guide

Full multi-client configuration reference for the Mobius MCP server.
This is the standalone document — the SKILL.md has a condensed summary.

## Connection Details

| Field | Value |
|-------|-------|
| Transport | Streamable HTTP (JSON-RPC over POST) |
| URL | `https://mobius.feedmob.com/api/mcp` |
| Auth Header | `Authorization: Bearer mob_...` |
| Protocol version | `2024-11-05` |
| Session required | No (stateless) |
| Tool count | 23 |
| Server name | `mobius` |

## Getting Your Token

1. Log in to Mobius → Settings → API & Tokens
2. Generate new token (starts with `mob_`)
3. Personal token = actions attributed to you; shared token = attributed to "Mobius AI"

## Client Configurations

### Hermes Agent (`~/.hermes/config.yaml`)

```yaml
mcp_servers:
  mobius:
    url: "https://mobius.feedmob.com/api/mcp"
    headers:
      Authorization: "Bearer mob_YOUR_TOKEN"
    timeout: 180
```

Restart Hermes → 23 tools registered as `mcp_mobius_*`.

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "mobius": {
      "url": "https://mobius.feedmob.com/api/mcp",
      "headers": {
        "Authorization": "Bearer mob_YOUR_TOKEN"
      }
    }
  }
}
```

If native HTTP doesn't work, use mcp-remote bridge:
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

### Cursor (`mcp.json`)

```json
{
  "mcpServers": {
    "mobius": {
      "url": "https://mobius.feedmob.com/api/mcp",
      "headers": {
        "Authorization": "Bearer mob_YOUR_TOKEN"
      }
    }
  }
}
```

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

Paste this to any AI agent to have it auto-configure:

```
I need you to add the Mobius MCP server to your configuration.

Connection details:
- Transport: Streamable HTTP
- URL: https://mobius.feedmob.com/api/mcp
- Auth header: Authorization: Bearer <MY_MOBIUS_TOKEN>
- Protocol version: 2024-11-05

The server exposes 23 tools (prefixed mcp_mobius_*) for issue tracking:
READ: list_issues, get_issue, list_teams, list_projects, list_users,
      list_labels, list_attachments, workspace_briefing, ask_mobius
WRITE: create_issue, update_issue, add_comment, update_comment,
       delete_comment, archive_issue, unarchive_issue, create_project,
       update_project, upload_attachment, delete_attachment,
       triage_issue, add_issue_link, remove_issue_link

Steps:
1. Find your MCP server config file.
2. Add an entry under mcp_servers named "mobius" with the URL and headers above.
3. Restart to discover tools.
4. Verify by calling list_teams — you should see teams like "AI", "Ad Operations".
```

## All 23 MCP Tools

### Read (9)

| Tool | Key Parameters |
|------|----------------|
| `list_issues` | `teamKey`, `stateType`, `assigneeEmail`, `labels`, `query`, `limit`, `cursor`, `sortBy` |
| `get_issue` | `identifier` (e.g. `"AI-1234"`) |
| `list_teams` | — |
| `list_projects` | — |
| `list_users` | — |
| `list_labels` | — |
| `list_attachments` | `identifier` |
| `workspace_briefing` | — |
| `ask_mobius` | `question` |

### Write (9)

| Tool | Key Parameters |
|------|----------------|
| `create_issue` | `teamKey`*, `title`*, `description`, `priority`, `labels`, `assigneeEmail`, `parentIdentifier` |
| `update_issue` | `identifier`*, `stateName`, `priority`, `assigneeEmail`, `labels`, `dueDate`, `projectName` |
| `add_comment` | `identifier`*, `body`* |
| `update_comment` | `commentId`*, `body`* |
| `delete_comment` | `commentId`* |
| `archive_issue` | `identifier`* |
| `unarchive_issue` | `identifier`* |
| `create_project` | `name`*, `description`, `status`, `leadEmail`, `teamKeys` |
| `update_project` | `name`*, `status`, `health`, `leadEmail`, `targetDate` |

### Attachments & Links (4)

| Tool | Key Parameters |
|------|----------------|
| `upload_attachment` | `filename`*, `mimeType`*, `dataBase64` or `fileUrl`, `identifier` |
| `delete_attachment` | `id`* |
| `add_issue_link` | `identifier`*, `url`*, `title`, `kind` |
| `remove_issue_link` | `id`* |

### AI Intelligence (1)

| Tool | Key Parameters |
|------|----------------|
| `triage_issue` | `identifier`*, `apply` |

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
| `canceled` | Canceled |

### Team Keys

| Team | Key |
|------|-----|
| AI Team (ai-team) | `AI` |
| Ad Operations | `ADO` |
| Platform | `PLT` |
| Data & Analytics | `DATA` |

## Troubleshooting

- **401 Unauthorized** — Token missing/expired. Regenerate in Mobius settings.
- **No tools discovered** — Verify URL is `/api/mcp` (not `/mcp`). Check VPN if off-network.
- **Unknown argument error** — Mobius MCP rejects unknown params (doesn't ignore them).
- **Comments show as "Mobius AI"** — Using shared token. Switch to personal token.

## Technical Notes (discovered via live probing)

- `GET /api/mcp` returns 405 with hint: "send JSON-RPC via POST"
- `POST /api/mcp` without Authorization returns `{"error":{"code":-32001,"message":"Unauthorized"}}`
- No `Mcp-Session-Id` header returned or required — fully stateless
- Server instructions field lists tool categories: "Read with list_issues/get_issue/...; write with create_issue/update_issue/..."
