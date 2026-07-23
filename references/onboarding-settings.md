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
   - Check `$MOBIUS_API_KEY` is set and valid.
   - If missing, ask the user to get a token from Mobius settings or the Mobius admin.
   - After key is set, verify teams, labels, projects, and state IDs with read-only queries.
3. **Auto-discover workspace context:**
   - `GET /api/teams` — discover teams and members
   - `GET /api/labels` — discover available labels
   - `GET /api/projects` — discover projects
   - `GET /api/issues?teamId=<uuid>&limit=5` — sample issues to confirm state IDs
4. **Present discovered defaults** to the user for confirmation.
5. **Write only confirmed, non-secret values** to `settings.md`.

## Required Settings Shape

```markdown
# Mobius Ticket Pilot Settings

Last verified: YYYY-MM-DD

## Mobius

- Instance: mobius.feedmob.com
- Default team: ai-team (AI)
- Default team ID: <uuid>
- User name: <name>
- Default project: AI team Action
- Default project ID: <uuid>
- Default labels: <comma-separated>
- Status mapping:
  - Start: In Progress
  - Review: In Review
  - Complete: Done
  - Blocked: <team status or blank>

## Auth Method

- Mobius: API key ($MOBIUS_API_KEY)

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

- Mobius API returns auth failure or unexpected response.
- The user says they changed workspace, team, or permissions.
- A write action would affect a different assignee or team than the saved defaults.
- State IDs change (Mobius re-deployed) — re-discover from `GET /api/issues`.
