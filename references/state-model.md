# Mobius State Model

## Status Types

Mobius uses 6 state types:

| Type | Typical names | Meaning |
|------|--------------|---------|
| `backlog` | Backlog | Acknowledged, not planned |
| `unstarted` | Todo | Planned, not started |
| `started` | In Progress, In Review | Actively being worked on |
| `completed` | Done | Finished |
| `canceled` | Canceled | Won't do |
| `duplicate` | Duplicate | Duplicate |

## Default Mapping

| Intent | State name | State type |
|--------|-----------|-----------|
| Not started | Backlog or Todo | backlog / unstarted |
| Working | In Progress | started |
| Human review | In Review | started |
| Complete | Done | completed |
| Won't do | Canceled | canceled |

## Changing State

To change an issue's state, PATCH with the state's UUID:

```bash
curl -s -X PATCH https://mobius.feedmob.com/api/issues/{issueUUID} \
  -H "Authorization: Bearer $MOBIUS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"stateId": "<state-uuid>"}'
```

**Always verify state UUIDs by reading an existing issue first.** State IDs are
per-team and may change if Mobius is re-deployed.

## Comment Contract

Post comments at these points:

### 1. Start comment
- Issue accepted
- Scope and first planned step

### 2. Phase milestone comments
- A logical chunk of work completed
- Key output produced

### 3. Blocker comment
- Exact symptom and error
- What the user must check

### 4. Completion comment
- Result summary
- Verification result
- Remaining steps

## Completion Rules

Use `In Review` when:
- A human review is needed.
- Verification passed locally but production check is pending.

Use `Done` when:
- Work is complete and verified.
- No further action needed.

Do not mark `Done` only because something was pushed — verify first.
