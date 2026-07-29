# Changelog

All notable changes to this project will be documented in this file.

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
