# Mobius Issue Audit Workflow

Read-only team issue priority analysis. **Never modify issues during an audit.**

## When to Run

- User says "整理整理最新情况" / "分析优先级" / "看看哪些值得推的"
- Regular cadence: every 2-5 days (e.g. a Mon/Wed/Fri rhythm)
- After team meetings that produce many new issues

## Mode A — MCP calls (preferred, all read-only)

1. **Active issues**: for each `stateType` in `backlog`, `unstarted`, `started`, call
   `list_issues(teamKey="AI", stateType=<type>, limit=200)` and keep calling with
   `cursor=nextCursor` while `hasMore` is true. One call per type is NOT enough once a
   bucket exceeds 200.
   - Useful extras: `sortBy="updated", sortOrder="asc"` surfaces the stalest first;
     `noAssignee=true` lists unassigned; `stateNames=["In Review"]` lists 待验收;
     `updatedBefore=<ISO date 60d ago>` lists ancient items.
2. **Key issue details**: `get_issue(identifier)` — description (incl. `### AI 理解`),
   comments, links and recent activity in one call. Fetch only the issues you will
   actually discuss.
3. **Per-person breakdown**: same rules as below (assignee AND labels); in mode A you
   can also filter server-side with `labels=["Alice"]` or `assigneeEmail="..."`.

Do not call `workspace_briefing` / `ask_mobius` as part of the routine audit — they
spend Mobius AI credits. Use them only when the user asks.

## Mode B — REST calls (fallback, all read-only)

### 1. Full active issue list

```python
import requests

headers = {"Authorization": f"Bearer {MOBIUS_API_KEY}"}
# teamId filter is CRITICAL — without it, returns ALL teams' issues
r = requests.get(
    f"https://mobius.feedmob.com/api/issues?teamId={TEAM_ID}&limit=500",
    headers=headers, timeout=30
)
issues = r.json()
active = [i for i in issues if i["state"]["type"] not in ("completed", "canceled", "duplicate")]
```

### 2. Key issue details (with comments + AI context)

```python
# Fetch in batches of 8-10 with 0.3s delay to be gentle
for identifier in key_issue_ids:
    r = requests.get(
        f"https://mobius.feedmob.com/api/issues/{identifier}?include=comments",
        headers=headers, timeout=10
    )
    # The description field contains "### AI 理解" section — meeting transcript enrichment
    time.sleep(0.3)
```

### 3. Per-person breakdown

Match issues to people using BOTH assignee AND labels (Mobius assignee is single-user;
labels carry multi-person ownership):

```python
for person in KEY_PEOPLE:  # lowercase names from settings.md → Key people
    person_issues = [
        i for i in active
        if person in (i.get("assignee",{}).get("name","") or "").lower()
        or person in " ".join(l["name"].lower() for l in i.get("labels",[]))
    ]
```

## Classification Patterns

| Pattern | Detection | Action |
|---------|-----------|--------|
| **Stuck In Review** | `state.name == "In Review"` and days since update > 14 | 🔴 Flag for immediate verification |
| **Ancient issues** | Active > 60 days, no update > 10 days | ⚪ Suggest Cancel |
| **Issue clusters** | 3+ issues with same keyword in title (e.g. the same product or tool name) | Suggest merge to main issue |
| **Suspected overlap** | 2 issues share surface keywords (e.g. both mention the same vendor) | ⚠️ MUST read comments+description on BOTH before flagging as overlap. Title similarity alone is misleading — could be upstream/downstream dependency, not duplication. |
| **Unassigned** | `assignee == null` and labels empty or `[未分配]` | Flag for assignment |
| **Overloaded** | Person with > 15 active issues | Note in per-person summary |
| **New direction** | Issues created by team leadership (who counts is listed in settings) | Priority — direction change |
| **In Review drought** | Only 1-2 issues in In Review across whole team | Either clear backlog or note nothing to verify |

## Output Format

### ⚠️ Format rule — ANALYSIS-DRIVEN, NOT EXHAUSTIVE LISTING

The user has corrected this repeatedly. The report is a **management tool for
priority decisions**, NOT a data export. Rules:

1. **Use 8-column tables** for all issues you DO include — never replace tables
   with prose/narrative. The table format is non-negotiable.
2. **Do NOT list every active issue.** Only include issues that are:
   - Stuck (no update > 10 days, zero comments, blocked)
   - In Review (need verification — the biggest bottleneck)
   - Unassigned (especially Mobius self-bugs)
   - Ancient (> 60 days — suggest Cancel)
   - Overlapping/clustered (need merge/split decision)
   - Key people deep-dives (from settings — their top items only)
   - Notable shifts from last report (new batches, sudden progress)
3. **Omit** routine "正常推进" Todo/Backlog items unless they're ancient or unusual.
   Do NOT pad the report with 30+ Todo items just for completeness.
4. A short 总览 table (totals + per-person counts) at the top is always included.

### 8-column table

```markdown
| Issue | 状态 | Label(→负责人) | 创建 | 最后更新 | 简介 | 建议原因 | 建议处理方式 |
```

- **Issue**: linked, format `[AI-XXXX](https://mobius.feedmob.com/issue/AI-XXXX)`
- **Label(→负责人)**: format `Label1, Label2 → Assignee` (arrow separates labels from assignee; use `—` if none)
- **创建 / 最后更新**: `MM-DD` format (short, not full dates)
- **简介**: 1-line title summary (≤ 30 chars if possible)
- **建议原因**: WHY this suggestion (1 sentence — last comment date, zero comments, stuck duration, etc.)
- **建议处理方式**: concrete action (验收→Done, 分配给X, 确认Cancel, 正常推进, etc.)

### Report structure (analysis-driven sections)

1. **总览** — 1 small table (totals + per-person counts) + 2-3 sentence trend readout
2. **In Review 堆积** — ALL In Review issues (these are the primary push targets)
3. **未分配** — ALL unassigned issues (especially Mobius self-bugs → the Mobius maintainer)
4. **重点开发人员分析** — Per-person deep dive tables (Key people from settings),
   showing only their **stuck/old/notable items** — NOT every issue they own.
   Add a 2-3 sentence summary per person: what they shipped, what's stuck, what to push.
5. **Top 5 建议优先推动** — short summary table at the very end (the only curated ranking)

**Do NOT** group by priority tiers (🔴/🟡/🟠) or by raw Mobius state for the whole report.
The report is organized by *what needs attention*, with per-person sections for context.

Also note: the last column is **建议处理方式** (suggested action), not 处理结果 (result).

## Key People to Track

Read the *Key people* list from `~/.mobius-ticket-pilot/settings.md` (name + what to
watch for each, e.g. "highest load", "accumulates issues", "long-stuck research").
Always add **the user** (their own backlog) and **Unassigned** (multi-person tasks).
If the list is missing, ask the user who to break out — do not guess from issue counts
alone, and do not write notes about colleagues into this repo.

## State IDs

Mode A needs none. Mode B: read them from `~/.mobius-ticket-pilot/ids.json`
(see SKILL.md → *Team-specific IDs*).

## Sync the report (optional)

If settings define a *Report sync path* (e.g. a notes vault), save the report there as
`<path>/<team>-Issue优先级分析-YYYYMMDD-Mobius.md`. If that folder is a git repo the user
syncs, commit and push only when the user has asked for it:

```bash
cd "<report sync repo>"
git add "<relative path to report>"
git commit -m "Add team issue analysis YYYY-MM-DD (...active, ...)"
git pull --rebase && git push
```

## ID Migration Note

Linear → Mobius migration changed issue numbers (e.g. Linear AI-1000 → Mobius AI-1029).
When comparing across historical reports, match by title content, not issue number.
