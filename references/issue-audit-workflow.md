# Mobius Issue Audit Workflow

Read-only team issue priority analysis. **Never modify issues during an audit.**

## When to Run

- User says "整理整理最新情况" / "分析优先级" / "看看哪些值得推的"
- Regular cadence: every 2-5 days (the user's team does Mon/Wed/Fri rhythm)
- After team meetings that produce many new issues

## API Calls (all read-only)

### 1. Full active issue list

```python
import requests

headers = {"Authorization": f"Bearer {MOBIUS_API_KEY}"}
# teamId filter is CRITICAL — without it, returns ALL teams' issues
r = requests.get(
    f"https://mobius.feedmob.com/api/issues?teamId={TEAM_AI_ID}&limit=500",
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
for person in ["Teammate-A", "Teammate-B", "Teammate-C", "Teammate-D", "Teammate-E", "the user"]:
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
| **Issue clusters** | 3+ issues with same keyword in title (e.g. "Team-X", "claude code") | Suggest merge to main issue |
| **Suspected overlap** | 2 issues share surface keywords (e.g. both mention "a vendor") | ⚠️ MUST read comments+description on BOTH before flagging as overlap. Title similarity alone is misleading — could be upstream/downstream dependency, not duplication. |
| **Unassigned** | `assignee == null` and labels empty or `[未分配]` | Flag for assignment |
| **Overloaded** | Person with > 15 active issues | Note in per-person summary |
| **New direction** | Issues created by Lead or with `lead_created` label | Priority — direction change |
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
   - Key developer deep-dives (Teammate-B/Teammate-A/Teammate-C — their top items only)
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
3. **未分配** — ALL unassigned issues (especially Mobius self-bugs → Teammate-A)
4. **重点开发人员分析** — Per-person deep dive tables (Teammate-B/Teammate-A/Teammate-C/Teammate-D),
   showing only their **stuck/old/notable items** — NOT every issue they own.
   Add a 2-3 sentence summary per person: what they shipped, what's stuck, what to push.
5. **Top 5 建议优先推动** — short summary table at the very end (the only curated ranking)

**Do NOT** group by priority tiers (🔴/🟡/🟠) or by raw Mobius state for the whole report.
The report is organized by *what needs attention*, with per-person sections for context.

Also note: the last column is **建议处理方式** (suggested action), not 处理结果 (result).

## Key People to Track

For FeedMob ai-team (AI), always break out these people:
- **Teammate-A** — highest load typically, main Mobius developer
- **Teammate-B** — tends to accumulate issues, Claude Code spec work
- **Teammate-C** — has most ancient stuck issues historically
- **Teammate-D** — ad research, tends to have long-stuck issues
- **the user** — the user (note her own backlog separately)
- **Unassigned** — multi-person tasks with no assignee set

## State ID Quick Reference (ai-team, verify before use)

```
Backlog:      <id>
Todo:         <id>
In Progress:  <id>
In Review:    <id>
Done:         <id>
Canceled:     <id>
```

## Sync to notes

Output file: `<notes-vault>/<notes folder>/AI-team-Issue优先级分析-YYYYMMDD-Mobius.md`

```bash
cd ~/<notes-vault>
git add "<notes folder>/AI-team-Issue优先级分析-YYYYMMDD-Mobius.md"
git commit -m "Add AI team issue analysis YYYY-MM-DD Mobius (...active, ...)"
git pull --rebase origin main
git push origin main
```

## ID Migration Note

Linear → Mobius migration changed issue numbers (e.g. Linear AI-1234 → Mobius AI-1234).
When comparing across historical reports, match by title content, not issue number.
