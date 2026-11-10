# Mobius Onboarding Settings

Use this reference when first configuring the Mobius agent loop or when the user asks to change defaults.

## Settings Path

```text
~/.mobius-ticket-pilot/settings.md
```

Create the parent directory if needed. The file is a local, user-specific defaults document,
**not** a credential store.

## First-Run Flow

1. **Check whether the settings file exists** and has the required sections.
2. **Verify Mobius access.**
   - **Mode A (MCP, preferred):** if Mobius MCP tools are available, call `whoami`.
     If the `mobius` server exists but needs auth, ask the user to sign in
     (Claude Code: `/mcp` → `mobius` → Authenticate). See `mcp-setup-guide.md`.
   - **Mode B (REST):** check `$MOBIUS_API_KEY` is set and valid. If missing, offer
     OAuth setup first; only fall back to asking for a token if MCP is not an option.
3. **Auto-discover workspace context** (read-only):
   - Mode A: `list_teams`, `list_labels`, `list_projects`, `list_users`
     (state IDs are not needed — MCP takes state names).
   - Mode B: `GET /api/teams`, `GET /api/labels`, `GET /api/projects`,
     `GET /api/issues?teamId=<uuid>&limit=5` to confirm state IDs.
4. **Present discovered defaults** to the user for confirmation.
5. **Write only confirmed, non-secret values** to `settings.md`.

## Required Settings Shape

```markdown
# Mobius Ticket Pilot Settings

Last verified: YYYY-MM-DD

## Mobius

- Instance: mobius.feedmob.com
- Default team: ai-team (AI)
- Default team key: AI
- Default team ID: <uuid>   # mode B only
- User name: <name>
- Default project: AI team Action
- Default project ID: <uuid>   # mode B only
- Default labels: <comma-separated>
- Status mapping:
  - Start: In Progress
  - Review: In Review
  - Complete: Done
  - Blocked: <team status or blank>

## Auth Method

- Mobius: MCP OAuth   # or: API key ($MOBIUS_API_KEY)

## Notes

- <non-secret team preferences>
```

## Never Store

Never write these to `settings.md` or any file:

- Mobius API keys (`mob_...` tokens)
- Session tokens, cookies, bearer tokens
- Personal credentials of any kind

## Revalidation Rules

Reuse saved defaults on future runs, but revalidate when:

- Mobius returns auth failure (401) or an unexpected response.
- `whoami` reports a different identity or `kind` than the saved one.
- The user says they changed workspace, team, or permissions.
- A write action would affect a different assignee or team than the saved defaults.
- State IDs change (Mobius re-deployed) — re-discover from `GET /api/issues`.
