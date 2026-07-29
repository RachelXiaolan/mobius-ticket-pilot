---  
name: mobius-ticket-pilot
description: >
  Mobius Ticket Pilot: read and manage Mobius (FeedMob internal issue tracker) issues.
  Works with any agent (Hermes, Codex, Claude Code, OpenClaw, Cursor, Gemini CLI).
  Use when the user asks to read/create/update Mobius issues, check team progress,
  analyze issue priorities, post progress comments, or change issue status.
  Designed for FeedMob's internal Mobius system (mobius.feedmob.com).
version: 1.0.2
author: Rachel Lu
license: MIT
platforms: [linux, macos]
prerequisites:
  env_vars: [MOBIUS_API_KEY]
  commands: [curl, python3]
tags: [Mobius, FeedMob, Issues, Project Management, Automation, Internal Tools]
---

# Mobius Ticket Pilot

## Overview

Read and manage issues on **Mobius** — FeedMob's internal issue tracking system
(built by Teammate-A, replacing Linear for ai-team).

- **Mobius** = task control plane AND artifact store (no GitHub sync needed).
- **This skill** = read issues, post comments, update status, analyze priorities,
  create new issues, track team progress — all via Mobius REST API.

Unlike the Linear ticket-pilot, there is **no GitHub mirror** — Mobius is a
self-contained internal tool. All issue tracking, comments, and status live on Mobius.

### Agent compatibility

This skill uses the [Agent Skills open standard](https://agentskills.io).
Any agent that supports `SKILL.md` + YAML frontmatter can use it.

Install with curl:
```bash
curl -fsSL https://raw.githubusercontent.com/RachelXiaolan/mobius-ticket-pilot/main/install.sh | bash
```

## Authentication

Mobius uses a **Bearer API token** (MCP key format: `mob_...`).

1. Get a token from Mobius settings (or ask the Mobius admin — currently Teammate-A).
2. Set it as `MOBIUS_API_KEY` environment variable.

Quick test:
```bash
curl -s https://mobius.feedmob.com/api/teams \
  -H "Authorization: Bearer $MOBIUS_API_KEY" | python3 -m json.tool
```

**Security:** Treat tokens as one-time secrets. Never store in files, git, comments, or logs.

## API Reference

### Base URL
```
https://mobius.feedmob.com
```

### Headers
```
Authorization: Bearer <MOBIUS_API_KEY>
Content-Type: application/json
```

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/issues?limit=N` | List issues (default returns all) |
| GET | `/api/issues/{identifier}` | Get single issue detail |
| GET | `/api/issues/{identifier}?include=comments` | Get issue with comments |
| GET | `/api/teams` | List all teams + members |
| GET | `/api/labels` | List all labels |
| GET | `/api/projects` | List all projects |
| POST | `/api/issues` | Create new issue |
| POST | `/api/issues/{id}/comments` | Add comment (uses UUID or identifier) |
| PATCH | `/api/issues/{id}` | Update issue (status, title, assignee, labels, etc.) |
| DELETE | `/api/issues/{id}` | Delete issue (use sparingly — prefer Canceled state) |

### Query Parameters for GET /api/issues

| Param | Example | Effect |
|-------|---------|--------|
| `limit` | `limit=500` | Max results (default may be lower) |
| `teamId` | `teamId=<uuid>` | Filter by team |
| `stateType` | `stateType=started` | Filter by state type: `backlog`, `unstarted`, `started`, `completed`, `canceled`, `duplicate` |
| `labelId` | `labelId=<uuid>` | Filter by label |
| `projectId` | `projectId=<uuid>` | Filter by project |
| `q` | `q=bidding` | Full-text search (use `q`, NOT `search`) |

**⚠️ Important:** `q` is the working search param. `search` and `query` do NOT filter.
Similarly, `state` and `label` (by name) appear to return all issues — use `stateType` 
and `labelId` for real filtering.

### State Types

Mobius uses 6 state types (same conceptual model as Linear):

| Type | Typical names | Meaning |
|------|--------------|---------|
| `backlog` | Backlog | Acknowledged, not planned |
| `unstarted` | Todo | Planned, not started |
| `started` | In Progress, In Review | Actively being worked on |
| `completed` | Done | Finished |
| `canceled` | Canceled | Won't do |
| `duplicate` | Duplicate | Duplicate of another issue |

**State IDs are per-team.** Each team has its own set of state UUIDs.
Always look up the state ID from the issue's `state.id` field, or query
existing issues to discover the UUIDs.

### ai-team (AI) Known State IDs

```
Backlog:      <id>
Todo:         <id>
In Progress:  <id>
In Review:    <id>
Done:         <id>
Canceled:     <id>
Duplicate:    <id>
```

> **⚠️ These IDs are specific to the ai-team (AI) workspace as of 2026-07-23.**
> If Mobius is re-deployed or a new team is added, these UUIDs will change.
> Always verify by querying an existing issue first.
> **Revalidation:** if `PATCH stateId` returns 400, re-discover state IDs by
> `GET /api/issues?teamId=<uuid>&stateType=<type>` and reading `state.id`.

### Known Team/Label/Project IDs

```
Team ai-team (AI):    <id>
Project AI team Action: <id>

Labels (by name):
  <your label>:   <id>
  Teammate-B:         <id>
  Teammate-C:        <id>
  Teammate-A:   <id>
  Teammate-D:       <id>
  Teammate-E:       <id>
  Lead:         <id>
  Teammate-F:     <id>
  全员:         <id>
  未分配:       <id>
  Teammate-G:         <id>
  Bug:         <id>
  Urgent:      <id>
  Feature:     <id>
```

## CLI Helper

For faster one-liners, use the Python CLI helper:

```bash
SCRIPT="$(find ~/.hermes ~/.claude ~/.codex ~/.openclaw 2>/dev/null -path '*/mobius-ticket-pilot/scripts/mobius_cli.py' | head -1)"
python3 "$SCRIPT" list-active
python3 "$SCRIPT" get AI-1234
python3 "$SCRIPT" get AI-1234 --comments
python3 "$SCRIPT" update-status AI-1234 "In Review"
python3 "$SCRIPT" add-comment AI-1234 "Starting work on this"
python3 "$SCRIPT" create "issue title" --description "body" --label "<your label>"
python3 "$SCRIPT" search "bidding"
python3 "$SCRIPT" team-status
```

See `scripts/mobius_cli.py` for all commands.

## Intent Detection — Read vs Write

**Before doing anything**, determine the user's intent:

| User says | Intent | What to do |
|-----------|--------|------------|
| "看一下 AI-1234" / "看看这个 issue" / "什么情况" | **Read-only** | Read the issue, summarize it, STOP. Do NOT change anything. |
| "帮我看看团队在做什么" / "看看大家进度" / "整理整理" | **Read-only** | Query and summarize team status. Do NOT modify. |
| "开始做 AI-1234" / "处理 AI-1234" / "搞一下这个" | **Start work** | Run the Start Workflow below. |
| "AI-1234 做完了" / "改完了" | **Complete work** | Verify, move to In Review/Done, post completion comment. |
| "建个 issue：xxx" | **Create** | Create new issue with proper naming convention. |
| Unclear | **Ask** | "你是想让我看一下这个 issue，还是开始做？" |

**Critical:** When in doubt, default to **read-only**.

## Team Naming Conventions

FeedMob ai-team (AI) issue naming pattern:

```text
#YYYYMMDD-NameN 描述内容
```

Examples:
- `#20260101-Name-01 做一个mcp的使用说明 doc（中英文）`
- `#20260101-Name-03 claude code 规范先出一版`

Description body:
```text
提出日期: YYYY-MM-DD
备注: 来源：... Action（... ）。
```

**Always sample 10+ recent issues first** to confirm the pattern before creating.

## Label & Assignee Rules

Mobius assignee is a single user field (same as Linear). For multi-person tasks,
use **labels** to indicate all participants.

- **Default assignee = current user** (from settings).
- **Default label = user's personal label** (e.g. `<your label>`). Always attach.
- **If the issue involves other teammates** — ask which labels to add. Do not guess.
- **Never remove or change someone else's label/assignee** without asking.

## Start Workflow

**Only enter when the user explicitly says to start work.**

1. **Resolve the target issue** from the user request (ID, URL, or query).
   - Read the issue with `?include=comments` to get full context + AI background.
2. **Confirm ownership and scope.** Apply Label & Assignee Rules.
3. **Mark work started.**
   - `PATCH /api/issues/{id}` with `stateId` = In Progress.
   - Post a comment with scope and first planned step.
4. **Do the work**, posting phase-based progress comments (see Comment Principles).
5. **On completion**, move to In Review or Done and post completion comment.

## Comment Principles

Comments are **phase-based, not prompt-based**:

1. Post when a **phase/chunk** completes, not every interaction.
2. Be concise — short and scannable.
3. Every comment MUST include:
   - **Who**: agent name or person
   - **What happened**: brief summary
   - **Key outputs**: links, results, or next step

Do NOT post a comment for every prompt. If 5 messages are part of "writing a report",
post ONE comment when the report is done.

## State Flow

```text
Backlog/Todo → In Progress → In Review → Done
```

- Use `Done` only when the user requested completion and verification passed.
- Use `In Review` when a human check is expected.
- Do not change state if the issue belongs to another assignee without consent.

## Team Visibility (Read-Only Analysis)

When the user asks to analyze priorities, check team progress, or review issues
("整理整理最新情况" / "分析优先级" / "看看哪些值得推的"), this is a **read-only** operation.
**Never modify any issue** — only read and report.

Quick summary:
1. `GET /api/issues?teamId=<uuid>&limit=500` — get all issues.
2. Filter active (exclude `completed`, `canceled`, `duplicate`).
3. Group by assignee AND labels (Mobius assignee is single-user; labels carry multi-person ownership).
4. Classify patterns (stuck, ancient, clusters, unassigned, overloaded, Lead's new direction).
5. **ALL issues MUST appear in the 8-column table** (see format below). Do NOT replace tables with prose/narrative summaries.
6. Group tables by Mobius state: **In Review → 未分配 → In Progress → Todo → Backlog**.
7. Add a Top 5 summary table at the end.
8. Sync to `<notes-vault>/<notes folder>/AI-team-Issue优先级分析-YYYYMMDD-Mobius.md`.

### ⚠️ Output format — NON-NEGOTIABLE

The user has corrected this: **every active issue goes into the 8-column table**, never into prose/narrative sections. Do not create custom section layouts, per-person narrative blocks, or bullet-list summaries as a substitute. The table IS the report.

```
| Issue | 状态 | Label(→负责人) | 创建 | 最后更新 | 简介 | 建议原因 | 建议处理方式 |
```

- **Issue**: linked, format `[AI-XXXX](https://mobius.feedmob.com/issue/AI-XXXX)`
- **Label(→负责人)**: format `Label1, Label2 → Assignee` (arrow separates labels from assignee)
- **建议原因**: WHY you're making this suggestion (1 sentence — last comment date, zero comments, stuck duration, etc.)
- **建议处理方式**: concrete next action (验收→Done, 分配给X, 确认Cancel, 正常推进, etc.)

Group the tables by state in this order: In Review (待验收) → 未分配 → In Progress → Todo → Backlog.
Then a short Top 5 table at the end with the most actionable items.

For the full audit workflow (batch fetching, classification patterns, tiered report
format, per-person breakdown, and notes sync), read
**`references/issue-audit-workflow.md`**.

### Label-as-assignee convention

Mobius assignee is a single user field. Multi-person tasks use **labels** to indicate
all participants. Always report label-based owners alongside the assignee:

| Assignee | Labels | Interpretation |
|----------|--------|---------------|
| Teammate-C | [Teammate-C] | Sole owner |
| null | [Teammate-B, the user] | Multi-person — both owners |
| Teammate-A | [Teammate-A, Teammate-B] | Teammate-A primary, Teammate-B collaborator |
| null | [未分配] | Truly unassigned — flag |

### Key people to track

For FeedMob ai-team (AI), always break out: **Teammate-A** (highest load, Mobius dev),
**Teammate-B** (accumulates issues), **Teammate-C** (most ancient stuck issues), **Teammate-D** (long-stuck
research), **the user** (the user — note her own backlog), and **Unassigned** (multi-person tasks).

## Credential Rules

- Ask for credentials only when needed.
- Treat tokens as one-time secrets. Never store in files, git, comments, or logs.
- Store stable non-secret defaults (team IDs, label IDs, naming conventions)
  only after explicit confirmation.
- **Do NOT save the Mobius API key to any file.** It goes in `MOBIUS_API_KEY` env var only.

## Onboarding

### Settings Path
```text
~/.mobius-ticket-pilot/settings.md
```

### First-Run Setup

1. **Verify Mobius access.** Test the API key:
   ```bash
   curl -s https://mobius.feedmob.com/api/teams -H "Authorization: Bearer $MOBIUS_API_KEY"
   ```
2. **Auto-discover workspace context** (read-only):
   - `GET /api/teams` — teams and members
   - `GET /api/labels` — available labels
   - `GET /api/projects` — available projects
   - `GET /api/issues?teamId=<uuid>&limit=5` — sample issues to learn state IDs
3. **Let user choose defaults:** default team, default project, default label(s).
4. **Save non-secret defaults** to `settings.md`.

Read `references/onboarding-settings.md` for the exact settings format.

## Mobius-Specific Features

### AI Background Enrichment

Mobius auto-generates an "AI 理解" (AI Understanding) section in issue descriptions,
derived from meeting transcripts (meeting-notes tool). This provides rich context that Linear
didn't have. Always read the full description when analyzing an issue.

### Issue Sources

- `source: "linear"` — migrated from Linear (historical data)
- `source: "mobius"` (or null) — created natively on Mobius
- `aiGenerated: true` — created by Mobius AI bot

### Multi-Agent Workflow Testing

Mobius supports automated issue creation by AI agents. Test issues may appear
in batches (e.g., PM→Architect→Developer→QA pipeline). These are usually
Canceled quickly after testing.

### Team Prefixes

| Prefix | Team |
|--------|------|
| `AI-` | ai-team (AI) |
| `ADO-` | Ad Operations |
| `DATA-` | Data & Insights |
| `INT-` | Integrations |
| `TEST-` | Testing (Teammate-A playbook tests) |

## Mobius MCP Server (HTTP endpoint)

In addition to the REST API, Mobius provides a built-in **MCP server** that exposes
23 tools — a strict superset of what REST can do.

| Capability | REST API | MCP |
|-----------|----------|-----|
| Read/write issues, comments, labels | ✅ | ✅ |
| Create/update projects | ❌ | ✅ |
| Upload/list/delete attachments | ❌ | ✅ |
| Add/remove external links | ❌ | ✅ |
| Archive (soft-delete) / unarchive | ❌ | ✅ |
| Edit/delete comments | ❌ | ✅ |
| AI triage (`triage_issue`) | ❌ | ✅ |
| AI workspace briefing | ❌ | ✅ |
| Natural-language Q&A (`ask_mobius`) | ❌ | ✅ |
| Hard delete issue | ✅ | ❌ |

**Endpoint:** `https://mobius.feedmob.com/api/mcp`
**Transport:** Streamable HTTP (JSON-RPC over POST, protocol `2024-11-05`)
**Auth:** Same Bearer token as REST (`Authorization: Bearer mob_...`)
**Session:** Stateless — no session-id required, every request carries the Bearer header.
**Tool prefix in Hermes:** `mcp_mobius_*` (e.g. `mcp_mobius_list_issues`)

### Hermes config (`~/.hermes/config.yaml`)

```yaml
mcp_servers:
  mobius:
    url: "https://mobius.feedmob.com/api/mcp"
    headers:
      Authorization: "Bearer mob_YOUR_TOKEN"
    timeout: 180
```

### MCP-only tools worth highlighting

- **`ask_mobius`** — Natural-language workspace Q&A with cited issue IDs. Faster than crafting REST queries for ad-hoc questions.
- **`workspace_briefing`** — AI-generated management briefing (headline + risks + recommendations). Great for weekly summaries.
- **`triage_issue`** — AI-suggests priority + labels for a new issue. Set `apply=true` to auto-apply.
- **`archive_issue`** — Soft-delete (recoverable). Prefer over REST's permanent `DELETE`.

### MCP personal vs. shared token

- **Personal token** (from your account settings): comments posted as *you*.
- **Shared/workspace token**: comments attributed to "Mobius AI" (bot account).
- For team use, prefer personal tokens so actions are traceable.

### Full MCP setup guide

For multi-client setup (Claude Desktop, Cursor, VS Code, Cline, Continue) and an
AI-agent quick-setup prompt, read **`references/mcp-setup-guide.md`**.

## Pitfalls

### Next.js SPA pages can't be read from saved HTML

Mobius is a Next.js App Router SPA. Saving a page as HTML yields only
"Loading Mobius…" — real content is rendered client-side from JS chunks.
To extract page structure, navigation labels, or i18n strings, fetch the JS
chunks directly and regex the i18n dictionary out of the bundle.
See `references/web-ui-navigation-analysis.md` for the full technique and
extracted structure, and `references/frontend-codebase.md` for the codebase
file map when you're ready to actually make UI changes.

### Web UI links MUST use `/issue/`, not `/all/`

The Mobius web UI (Next.js App Router) uses **`/issue/{identifier}`** for issue
detail pages. **`/all/{identifier}` is the board view** — it will NOT show the issue.

```
https://mobius.feedmob.com/issue/AI-1234    ← ✅ correct (issue detail page)
https://mobius.feedmob.com/all/AI-1234      ← ❌ WRONG (board view — blank/error)
```

**Always generate `/issue/AI-XXXX` links** in reports, comments, and notes files.
`/all/AI-XXXX` links open to a blank page.

### No pagination cursor — use limit

Unlike Linear's GraphQL cursor pagination, Mobius returns all issues in one call.
Use `limit=500` to be safe. There is no `after` cursor.

### Search param is `q`, not `search`

`?search=` and `?query=` do NOT filter — they return all issues.
Only `?q=` performs actual text search.

### State/label name filters don't work

`?state=todo` and `?label=Teammate-B` return ALL issues regardless.
Use `?stateType=started` and `?labelId=<uuid>` for real filtering.

### `?include=comments` only works on single issue detail

`GET /api/issues/{id}?include=comments` returns comments.
`GET /api/issues?include=comments` does NOT include comments in list mode.
To get comments for multiple issues, fetch each individually.

### Comments use POST, not GET

`GET /api/issues/{id}/comments` returns 405.
To read comments, use `GET /api/issues/{id}?include=comments`.
To post comments, use `POST /api/issues/{id}/comments`.

### DELETE is permanent

`DELETE /api/issues/{id}` permanently removes the issue.
For normal issue closure, use `PATCH` with `stateId` = Canceled instead.
Only use DELETE for test cleanup.

### ⚠️ PATCH `delegatedAgentId` triggers Mobius Agent auto-triage (SIDE EFFECTS)

Setting `delegatedAgentId` on an issue via PATCH **arms the Mobius Agent bot against that issue**. The agent then autonomously triages it — editing the title, rewriting the description, changing state, assigning labels, and **auto-creating sub-issues**. This all happens within seconds and is NOT reversible by unsetting the field.

```bash
# ❌ DANGEROUS on a real/production issue — triggers full auto-triage
curl -X PATCH -d '{"delegatedAgentId":"<agent_uuid>"}' \
  https://mobius.feedmob.com/api/issues/<issue_id>
```

**Do NOT use production issues to probe/explore this feature.** If you need to understand agent delegation, create a throwaway `TEST-` issue first, or observe it on an issue where triage is already desired. Unsetting `delegatedAgentId: null` after the fact stops future triage but does NOT undo the sub-issues/comments already created — those must be cleaned up manually (DELETE each sub-issue + post an explanatory comment).

This was learned the hard way: an exploratory PATCH on AI-1234 auto-generated AI-1234 within ~30s, requiring cleanup + an apology comment. Treat any write that touches agent/automation fields as a **write with side effects**, not a harmless probe.

### Issue overlap classification MUST read comments first

When flagging two issues as "overlapping" or "merge candidates", you MUST read the
full descriptions and at least the last 3 comments on both issues before concluding.
Title similarity alone is misleading — e.g. two issues both mentioning "a vendor
MCP" turned out to be completely different tasks (one = build API wrapper, the other =
compare official MCP vs self-built).

**Rule:** Never recommend Cancel/merge based on title keywords alone. Always run:
```python
r = requests.get(f"{BASE}/api/issues/{iid}?include=comments", headers=headers)
```
on both issues, then compare actual work direction, not surface keywords.

**If an overlap claim was already made in a report and turns out wrong:**
acknowledge the error directly ("我的判断失误——当时只看了标题就判了重叠建议合并"),
explain what the actual relationship is (often upstream/downstream dependency, not
duplication), and give the user a corrected recommendation to share with the team.

### State IDs are per-team and may change

The state UUIDs documented above are specific to ai-team (AI) as of 2026-07-23.
If Mobius is re-deployed, these will change. Always verify by reading an
existing issue's `state.id` before attempting a PATCH.

## Stop Conditions

Stop and ask the user when:
- A required action needs human approval.
- A credential is needed.
- Continuing would reassign someone else's issue.
- A write action would change visibility or affect external systems.
- The issue is unclear or ambiguous.

## Resources

- `scripts/mobius_cli.py` — Python CLI for common Mobius operations.
- `references/onboarding-settings.md` — first-run onboarding and settings format.
- `references/state-model.md` — Mobius state model and comment contract.
- `references/issue-audit-workflow.md` — read-only team priority analysis: batch fetching, classification patterns, tiered report format, per-person breakdown, notes sync, ID migration notes. Includes false-overlap detection rule.
- `references/mcp-setup-guide.md` — full Mobius MCP server setup: multi-client configs (Hermes, Claude Desktop, Cursor, Cline, Continue), all 23 tools, AI quick-setup prompt, troubleshooting.
- `references/web-ui-navigation-analysis.md` — Mobius web UI navigation structure (extracted from Next.js i18n bundle), page overlap diagnosis, 3-step redesign proposal for the Developers/Guide/Settings config flow. Use when proposing UI changes or debugging page routes.
- `references/frontend-codebase.md` — file map for contributing code to the Mobius repo (`<private Mobius repo>`): where pages/components/i18n live, i18n pattern, guide-content structure, verification commands, PR conventions. Read BEFORE editing the Mobius frontend.
- `references/agent-automation.md` — `/api/agents`, `/api/settings`, and the `delegatedAgentId` tripwire. Read BEFORE any exploratory PATCH on agent/triage fields — setting this field on a production issue auto-creates sub-issues and rewrites the description.
