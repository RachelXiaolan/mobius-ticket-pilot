# Mobius Ticket Pilot 🎫✈️

**A multi-agent Skill for managing Mobius (FeedMob internal issue tracker) issues.**

Mobius Ticket Pilot lets any AI Agent (Hermes, Claude Code, Codex, OpenClaw, Cursor, Gemini CLI) read and write FeedMob's internal issue tracking system, Mobius. The agent can:

- Read / create / update Mobius issues
- Analyze team issue priorities (read-only mode — modifies nothing)
- Post phase-based progress comments and update status
- Track team member workload and progress
- Operate via REST API or MCP Server

> **Difference from Linear ticket-pilot:** Mobius is self-contained — no GitHub mirror sync needed. All issues, comments, and status live on Mobius.

## Installation

### Option 1: curl one-liner (recommended)

```bash
# Default: install to Claude Code
curl -fsSL https://raw.githubusercontent.com/RachelXiaolan/mobius-ticket-pilot/main/install.sh | bash

# Specify agent (comma-separated for multiple)
curl -fsSL https://raw.githubusercontent.com/RachelXiaolan/mobius-ticket-pilot/main/install.sh | bash -s -- --agent hermes
curl -fsSL https://raw.githubusercontent.com/RachelXiaolan/mobius-ticket-pilot/main/install.sh | bash -s -- --agent claude,codex,hermes
```

Available agents: `claude` `codex` `hermes` `openclaw` `cursor` `gemini`

### Option 2: Manual

```bash
git clone https://github.com/RachelXiaolan/mobius-ticket-pilot.git
cp -r mobius-ticket-pilot/ ~/.claude/skills/mobius-ticket-pilot/    # or your agent's path
```

| Agent | Skills directory |
|-------|-----------------|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Hermes | `~/.hermes/skills/productivity/` |
| OpenClaw | `~/.openclaw/skills/` |
| Cursor | `.cursor/skills/` |
| Gemini CLI | `.gemini/skills/` |

## Prerequisites

### Mobius API Token

Mobius uses Bearer token auth (format: `mob_...`):

1. Get a token from Mobius settings (or ask the Mobius admin — currently Teammate-A)
2. Set as `MOBIUS_API_KEY` environment variable

```bash
export MOBIUS_API_KEY="mob_your_token_here"
```

Quick test:
```bash
curl -s https://mobius.feedmob.com/api/teams \
  -H "Authorization: Bearer $MOBIUS_API_KEY" | python3 -m json.tool
```

### System dependencies

- `curl` — API calls
- `python3` — CLI helper script

## Quick Start

After installation, just talk to your agent in natural language:

```
Look at AI-1234
```

The agent reads the issue and summarizes it — **without changing anything**.

```
Analyze team priorities, what's stuck?
```

The agent pulls all active issues, identifies bottlenecks, and generates a report.

### Common triggers

| What you say | What the agent does |
|-------------|-------------------|
| `看一下 AI-XXXX` / `look at AI-XXXX` | **Read-only**: summarize issue, change nothing |
| `分析优先级` / `analyze priorities` | **Read-only**: pull all active issues, generate priority report |
| `开始做 AI-XXXX` / `start working on AI-XXXX` | Read → In Progress → post "started" comment → work |
| `AI-XXXX 改完了` / `AI-XXXX is done` | Verify → In Review/Done → completion comment |
| `建个 issue：xxx` / `create issue: xxx` | Create with team naming conventions |
| Unclear | Agent asks: "Do you want to look, or start working?" |

> 💡 **"Look at" ≠ "Start working."** The agent won't change status just because you mentioned an issue. Only explicit "start/process/do" triggers the full workflow.

## Team Priority Analysis (Read-Only)

A core feature. When you say "analyze priorities" or "check team status":

1. Fetch all active issues (`GET /api/issues?teamId=<uuid>&limit=500`)
2. Filter out completed/canceled/duplicate
3. Group by owner, identify stuck issues
4. Output an **8-column table report**:

```
| Issue | Status | Label(→Owner) | Created | Last Updated | Summary | Reason | Suggested Action |
```

5. Focus areas: In Review backlog, unassigned issues, ancient zombie issues, developer workload
6. Sync to notes vault

**Entirely read-only — no issues are modified.**

## CLI Helper

```bash
SCRIPT="$(find ~/.hermes ~/.claude ~/.codex 2>/dev/null -path '*/mobius-ticket-pilot/scripts/mobius_cli.py' | head -1)"

python3 "$SCRIPT" list-active          # List active issues
python3 "$SCRIPT" get AI-1234          # Get single issue
python3 "$SCRIPT" get AI-1234 --comments   # With comments
python3 "$SCRIPT" update-status AI-1234 "In Review"  # Change status
python3 "$SCRIPT" add-comment AI-1234 "Starting"      # Post comment
python3 "$SCRIPT" create "Title" --description "Body" --label "<your label>"  # Create
python3 "$SCRIPT" search "bidding"     # Search
python3 "$SCRIPT" team-status          # Team overview
```

## Mobius MCP Server

In addition to REST API, Mobius provides a built-in MCP Server (23 tools, a superset of REST):

- AI tools: `triage_issue` / `workspace_briefing` / `ask_mobius`
- Soft delete (archive) / attachments / comment editing / project management / external links

Hermes config:
```yaml
mcp_servers:
  mobius:
    url: "https://mobius.feedmob.com/api/mcp"
    headers:
      Authorization: "Bearer mob_YOUR_TOKEN"
    timeout: 180
```

See `references/mcp-setup-guide.md` for multi-client setup (Hermes / Claude Desktop / Cursor / Cline / Continue).

## Key Design Decisions

1. **Read-only by default**: When intent is unclear, never modify issues
2. **Mobius = single source of truth**: No GitHub sync needed
3. **Label = actual owner**: Mobius assignee is single-user; multi-person tasks use labels
4. **Phase-based comments**: Post one comment per phase completed, not per prompt
5. **Web UI links use `/issue/`**: `/issue/AI-XXXX` is the detail page; `/all/AI-XXXX` is the board (blank)

## File Structure

```
mobius-ticket-pilot/
├── SKILL.md                              # Main skill file
├── README.md                             # Chinese README
├── README_EN.md                          # This file
├── LICENSE                               # MIT
├── CHANGELOG.md                          # Version history
├── install.sh                            # One-click installer
├── references/
│   ├── onboarding-settings.md            # First-run setup format
│   ├── state-model.md                    # Mobius state model + comment contract
│   ├── issue-audit-workflow.md           # Read-only team priority analysis workflow
│   ├── mcp-setup-guide.md               # MCP Server multi-client config guide
│   ├── web-ui-navigation-analysis.md     # Mobius frontend navigation structure
│   ├── frontend-codebase.md              # Mobius frontend codebase map (for PRs)
│   └── agent-automation.md               # Agent automation field pitfalls (delegatedAgentId)
└── scripts/
    └── mobius_cli.py                     # Python CLI helper
```

## License

MIT

## Author

Rachel Lu (@RachelXiaolan)
