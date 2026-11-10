# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-11-10

### Added
- **MCP-first access mode with OAuth.** SKILL.md now starts every task by detecting
  mode A (Mobius MCP tools present → use them) or mode B (REST + `MOBIUS_API_KEY`).
  Setup A documents OAuth sign-in for Claude Code (`claude mcp add` / `~/.claude.json`),
  claude.ai custom connectors and other MCP clients — no `mob_` token needed.
- SKILL.md: "Identity rules" — person vs paired agent, untrusted issue text, 401 = stop.
- SKILL.md: MCP equivalents for every lifecycle point (`update_issue` + `add_comment`
  with the same comment templates as `auto_progress.py`), plus agent run trailers.
- SKILL.md / `mcp-setup-guide.md`: all 32 MCP tools grouped, key `list_issues`
  parameters (`stateNames`, `labels`, `query`, `cursor`, `sortBy`…), people-only markers.
- `mcp-setup-guide.md`: OAuth discovery endpoints, agent pairing via `agent_guide`.
- `issue-audit-workflow.md`: mode A fetching with cursor pagination.

### Changed
- Team prefixes updated to the live list (AI, ADO, AS, BEES, FE, LAB, MOB, TEST);
  `DATA-` / `INT-` / `PLT-` marked stale.
- Pagination / search / name-filter pitfalls now say which mode they apply to
  (MCP: `query`, `cursor`, max 200 per page; REST: `q`, no cursor).
- Delegation pitfall covers MCP `delegateToEmail` as well as REST `delegatedAgentId`.
- `auto_progress.py` / `mobius_cli.py` documented as mode B tools (ai-team only).
- Onboarding: verify with `whoami`; settings record auth method and team key.
- READMEs: OAuth setup is option A, API token is option B.

### Fixed
- `install.sh`: `--agent claude,codex` comma lists now work (README already promised it).
- `install.sh`: without git it now downloads the full repo tarball; before, it fetched
  only 4 files and missed `auto_progress.py` and most references.
- `install.sh`: auto-detect now prefers Claude Code, matching the README.
- SKILL.md frontmatter opening `---` had trailing spaces.

## [1.1.0] - 2026-07-31

### Added
- `scripts/auto_progress.py` — **auto progress tracker**: automates state transition + formatted comment in one atomic command. 5 lifecycle points: `start` (🚀→In Progress), `progress` (💬 milestone), `blocker` (🛑 stuck), `review` (🎉→In Review), `done` (✅→Done)
- SKILL.md: new "Auto Progress Tracker (MUST USE)" section — Agent must call `auto_progress.py` at every lifecycle point instead of manually PATCH+POST
- SKILL.md: "When to call each command" guide with rule of thumb

### Changed
- SKILL.md: Start Workflow rewritten to reference `auto_progress.py` instead of manual PATCH+POST
- SKILL.md: version bumped to 1.1.0

## [1.0.2] - 2026-07-24

### Added
- `references/issue-audit-workflow.md` — complete read-only team priority analysis workflow: batch fetching, classification patterns, 8-column report format, per-person breakdown, notes sync, false-overlap detection rule
- `references/mcp-setup-guide.md` — full Mobius MCP server setup guide: 5 clients (Hermes, Claude Desktop, Cursor, Cline, Continue), all 23 tools documented, AI quick-setup prompt, troubleshooting
- `references/web-ui-navigation-analysis.md` — Mobius web UI navigation structure extracted from Next.js i18n bundle, page overlap diagnosis, redesign proposal
- `references/frontend-codebase.md` — file map for contributing to the Mobius frontend repo (`<private Mobius repo>`)
- `references/agent-automation.md` — `delegatedAgentId` tripwire documentation: setting this field triggers autonomous AI triage with irreversible side effects
- `scripts/mobius_cli.py` — Python CLI helper for common Mobius operations
- SKILL.md: Team Visibility section with 8-column report format spec
- SKILL.md: Mobius MCP Server section (23 tools, comparison table vs REST)
- SKILL.md: Issue overlap classification pitfall (must read comments before judging overlap)
- SKILL.md: `delegatedAgentId` pitfall (auto-creates sub-issues, learned the hard way on AI-1234)

### Fixed
- Web UI links must use `/issue/AI-XXXX` not `/all/AI-XXXX` (board view shows blank)
- SKILL.md Endpoints table was split by Web UI URL section (formatting broken)

## [1.0.0] - 2026-07-23

### Added
- Initial release
- Read/create/update/delete Mobius issues via REST API
- Team priority analysis (read-only, 8-column report)
- Phase-based progress comments
- Label-as-assignee convention for multi-person tasks
- CLI helper (`mobius_cli.py`)
- Onboarding and settings system
- `install.sh` one-click installer for 6 agents
- `references/onboarding-settings.md`
- `references/state-model.md`
