#!/usr/bin/env python3
"""
Mobius Ticket Pilot — Auto Progress Tracker

Automates the "post comments at key phases" contract so the Agent doesn't
forget.  The Agent calls ONE command at each lifecycle point; this script
handles state transitions + formatted comments atomically.

Lifecycle:
    start    → state → In Progress + 🚀 start comment
    progress → 💬 phase comment (state unchanged)
    blocker  → 🛑 blocker comment (state unchanged)
    review   → state → In Review + 🎉 completion comment
    done     → state → Done + ✅ done comment

Usage:
    python3 auto_progress.py start AI-1234 --scope "Scope description" --plan "First step"
    python3 auto_progress.py progress AI-1234 --summary "What was completed" --next "What's next"
    python3 auto_progress.py blocker AI-1234 --error "Error message" --check "What to check"
    python3 auto_progress.py review AI-1234 --summary "What was delivered" --links "https://..."
    python3 auto_progress.py done AI-1234 --summary "Final result" --links "https://..."

Requires MOBIUS_API_KEY environment variable.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_URL = "https://mobius.feedmob.com"

# ai-team (AI) state IDs as of 2026-07-23
STATE_IDS = {
    "backlog": "<id>",
    "todo": "<id>",
    "in_progress": "<id>",
    "in review": "<id>",
    "done": "<id>",
    "canceled": "<id>",
    "duplicate": "<id>",
}


def get_key():
    key = os.environ.get("MOBIUS_API_KEY", "")
    if not key:
        print("ERROR: MOBIUS_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    return key


def api(method, path, data=None):
    key = get_key()
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")[:500] if e.fp else str(e)
        print(f"HTTP {e.code}: {err}", file=sys.stderr)
        sys.exit(1)


def get_issue(identifier):
    """Get issue by identifier, returns full JSON."""
    return api("GET", f"/api/issues/{identifier}")


def set_state(issue_uuid, state_name):
    """PATCH issue to a new state."""
    state_key = state_name.lower().strip()
    state_id = STATE_IDS.get(state_key)
    if not state_id:
        print(f"ERROR: Unknown state '{state_name}'", file=sys.stderr)
        sys.exit(1)
    return api("PATCH", f"/api/issues/{issue_uuid}", {"stateId": state_id})


def post_comment(issue_uuid, body):
    """Post a comment to an issue."""
    return api("POST", f"/api/issues/{issue_uuid}/comments", {"body": body})


def issue_url(identifier):
    return f"{BASE_URL}/issue/{identifier}"


# ── Lifecycle handlers ──────────────────────────────────────────────

def do_start(args):
    """Start: set In Progress + post 🚀 start comment."""
    issue = get_issue(args.identifier)
    if not issue:
        print(f"Issue {args.identifier} not found.", file=sys.stderr)
        sys.exit(1)

    iid = issue["id"]
    title = issue.get("title", "")
    current_state = issue.get("state", {}).get("name", "")

    # Change state to In Progress (skip if already there)
    if current_state != "In Progress":
        set_state(iid, "in_progress")
        print(f"📋 State: {current_state} → In Progress")
    else:
        print(f"📋 State: already In Progress (skipping)")

    # Build and post comment
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [f"🚀 **开始处理**\n"]
    parts.append(f"*{now}*\n")
    if args.scope:
        parts.append(f"**范围:** {args.scope}\n")
    if args.plan:
        parts.append(f"**下一步:** {args.plan}\n")
    if args.branch:
        parts.append(f"**分支:** `{args.branch}`\n")
    parts.append(f"**Issue:** [{args.identifier}]({issue_url(args.identifier)})\n")

    post_comment(iid, "\n".join(parts))
    print(f"💬 Start comment posted on {args.identifier}")
    print(f"🔗 {issue_url(args.identifier)}")


def do_progress(args):
    """Progress: post 💬 phase milestone comment (no state change)."""
    issue = get_issue(args.identifier)
    if not issue:
        print(f"Issue {args.identifier} not found.", file=sys.stderr)
        sys.exit(1)

    iid = issue["id"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    parts = [f"💬 **进度更新**\n"]
    parts.append(f"*{now}*\n")
    if args.summary:
        parts.append(f"**完成:** {args.summary}\n")
    if args.output:
        parts.append(f"**产出:** {args.output}\n")
    if args.next:
        parts.append(f"**下一步:** {args.next}\n")

    post_comment(iid, "\n".join(parts))
    print(f"💬 Progress comment posted on {args.identifier}")
    print(f"🔗 {issue_url(args.identifier)}")


def do_blocker(args):
    """Blocker: post 🛑 blocker comment (no state change)."""
    issue = get_issue(args.identifier)
    if not issue:
        print(f"Issue {args.identifier} not found.", file=sys.stderr)
        sys.exit(1)

    iid = issue["id"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    parts = [f"🛑 **遇到阻塞**\n"]
    parts.append(f"*{now}*\n")
    if args.error:
        parts.append(f"**问题:** {args.error}\n")
    if args.check:
        parts.append(f"**需要检查:** {args.check}\n")

    post_comment(iid, "\n".join(parts))
    print(f"🛑 Blocker comment posted on {args.identifier}")
    print(f"🔗 {issue_url(args.identifier)}")


def do_review(args):
    """Review: set In Review + post 🎉 completion comment."""
    issue = get_issue(args.identifier)
    if not issue:
        print(f"Issue {args.identifier} not found.", file=sys.stderr)
        sys.exit(1)

    iid = issue["id"]
    current_state = issue.get("state", {}).get("name", "")

    if current_state != "In Review":
        set_state(iid, "in review")
        print(f"📋 State: {current_state} → In Review")
    else:
        print(f"📋 State: already In Review (skipping)")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [f"🎉 **完成，等待验收**\n"]
    parts.append(f"*{now}*\n")
    if args.summary:
        parts.append(f"**交付:** {args.summary}\n")
    if args.links:
        parts.append(f"**链接:** {args.links}\n")

    post_comment(iid, "\n".join(parts))
    print(f"💬 Review comment posted on {args.identifier}")
    print(f"🔗 {issue_url(args.identifier)}")


def do_done(args):
    """Done: set Done + post ✅ done comment."""
    issue = get_issue(args.identifier)
    if not issue:
        print(f"Issue {args.identifier} not found.", file=sys.stderr)
        sys.exit(1)

    iid = issue["id"]
    current_state = issue.get("state", {}).get("name", "")

    if current_state != "Done":
        set_state(iid, "done")
        print(f"📋 State: {current_state} → Done")
    else:
        print(f"📋 State: already Done (skipping)")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [f"✅ **已完成**\n"]
    parts.append(f"*{now}*\n")
    if args.summary:
        parts.append(f"**结果:** {args.summary}\n")
    if args.links:
        parts.append(f"**链接:** {args.links}\n")

    post_comment(iid, "\n".join(parts))
    print(f"💬 Done comment posted on {args.identifier}")
    print(f"🔗 {issue_url(args.identifier)}")


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Mobius auto progress tracker — handles state + comments at lifecycle points",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Lifecycle commands:
  start     → In Progress + 🚀 start comment
  progress  → 💬 phase comment (no state change)
  blocker   → 🛑 blocker comment (no state change)
  review    → In Review + 🎉 review comment
  done      → Done + ✅ done comment

Examples:
  %(prog)s start AI-1234 --scope "写 MCP 配置文档" --plan "先调研现有文档"
  %(prog)s progress AI-1234 --summary "414行文档完成" --next "提交PR"
  %(prog)s blocker AI-1234 --error "tsc有92个错误" --check "检查@types/node"
  %(prog)s review AI-1234 --summary "文档+2个PR" --links "https://github.com/.../pull/45"
  %(prog)s done AI-1234 --summary "PR merged" --links "https://github.com/.../pull/45"
        """,
    )
    sub = parser.add_subparsers(dest="lifecycle", required=True)

    # start
    p = sub.add_parser("start", help="Begin work: → In Progress + 🚀 comment")
    p.add_argument("identifier", help="Issue ID (e.g. AI-1234)")
    p.add_argument("--scope", default="", help="What will be done")
    p.add_argument("--plan", default="", help="First planned step")
    p.add_argument("--branch", default="", help="Git branch name (if any)")
    p.set_defaults(func=do_start)

    # progress
    p = sub.add_parser("progress", help="Phase milestone: 💬 comment only")
    p.add_argument("identifier", help="Issue ID")
    p.add_argument("--summary", default="", help="What was completed")
    p.add_argument("--output", default="", help="Key output/artifact produced")
    p.add_argument("--next", default="", help="Next step")
    p.set_defaults(func=do_progress)

    # blocker
    p = sub.add_parser("blocker", help="Stuck: 🛑 blocker comment")
    p.add_argument("identifier", help="Issue ID")
    p.add_argument("--error", default="", help="Error/symptom")
    p.add_argument("--check", default="", help="What user must check")
    p.set_defaults(func=do_blocker)

    # review
    p = sub.add_parser("review", help="Complete: → In Review + 🎉 comment")
    p.add_argument("identifier", help="Issue ID")
    p.add_argument("--summary", default="", help="What was delivered")
    p.add_argument("--links", default="", help="PR/URL links")
    p.set_defaults(func=do_review)

    # done
    p = sub.add_parser("done", help="Done: → Done + ✅ comment")
    p.add_argument("identifier", help="Issue ID")
    p.add_argument("--summary", default="", help="Final result")
    p.add_argument("--links", default="", help="Verification links")
    p.set_defaults(func=do_done)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
