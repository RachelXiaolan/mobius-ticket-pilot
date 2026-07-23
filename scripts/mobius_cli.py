#!/usr/bin/env python3
"""
Mobius Ticket Pilot — CLI helper for Mobius issue management.
Usage: python3 mobius_cli.py <command> [args]

Commands:
  list-active [--team TEAM_ID]          List active issues
  get IDENTIFIER [--comments]           Get issue detail (+ comments)
  search QUERY                          Full-text search
  team-status [--team TEAM_ID]          Team summary (per-person breakdown)
  create TITLE [--description D] [--label L] [--assignee A]  Create issue
  update-status IDENTIFIER --state STATE   Change issue state
  add-comment IDENTIFIER --body BODY    Add a comment
  assign IDENTIFIER --to USER_ID        Assign issue
  labels                                List all labels
  teams                                 List all teams
  projects                              List all projects
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_URL = "https://mobius.feedmob.com"

# Cached IDs (ai-team AI as of 2026-07-23)
STATE_IDS = {
    "backlog": "<id>",
    "todo": "<id>",
    "in_progress": "<id>",
    "in review": "<id>",
    "done": "<id>",
    "canceled": "<id>",
    "duplicate": "<id>",
}

TEAM_AI = "<id>"

LABEL_NAMES = {
    "the user": "<id>",
    "<your label>": "<id>",
    "Teammate-B": "<id>",
    "Teammate-C": "<id>",
    "Teammate-A": "<id>",
    "Teammate-D": "<id>",
    "Teammate-E": "<id>",
    "Lead": "<id>",
    "Teammate-F": "<id>",
}


def get_key():
    key = os.environ.get("MOBIUS_API_KEY", "")
    if not key:
        print("ERROR: MOBIUS_API_KEY environment variable not set.", file=sys.stderr)
        print("Get a token from Mobius settings or ask the Mobius admin.", file=sys.stderr)
        sys.exit(1)
    return key


def api(method, path, data=None):
    """Make a Mobius API call and return parsed JSON."""
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
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")[:500] if e.fp else str(e)
        print(f"HTTP {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def resolve_state_id(state_name):
    """Resolve a state name to its UUID (case-insensitive)."""
    key = state_name.lower().strip()
    if key in STATE_IDS:
        return STATE_IDS[key]
    # Try to discover from existing issues
    issues = api("GET", f"/api/issues?teamId={TEAM_AI}&limit=5")
    for i in issues:
        s = i.get("state", {})
        if s.get("name", "").lower() == key:
            return s["id"]
    print(f"ERROR: Unknown state '{state_name}'. Known: {', '.join(STATE_IDS.keys())}", file=sys.stderr)
    sys.exit(1)


def resolve_label_id(label_name):
    """Resolve a label name to its UUID."""
    key = label_name.lower().strip()
    if key in LABEL_NAMES:
        return LABEL_NAMES[key]
    # Search labels API
    labels = api("GET", "/api/labels")
    for l in labels:
        if l["name"].lower() == key:
            return l["id"]
    print(f"WARNING: Label '{label_name}' not found. Available: {', '.join(l['name'] for l in labels)}", file=sys.stderr)
    return None


def cmd_list_active(args):
    team_id = args.team or TEAM_AI
    issues = api("GET", f"/api/issues?teamId={team_id}&limit=500")
    active = [i for i in issues if i["state"]["type"] not in ("completed", "canceled", "duplicate")]
    active.sort(key=lambda x: x.get("createdAt", ""))

    print(f"Active issues: {len(active)} / {len(issues)} total\n")
    for i in active:
        assignee = i.get("assignee")
        aname = assignee.get("name", "N/A") if assignee else "N/A"
        labels = ", ".join(l["name"] for l in i.get("labels", []))
        print(f"{i['identifier']:8s} | {i['state']['name']:12s} | {aname:20s} | [{labels}] | {i['createdAt'][:10]}→{i['updatedAt'][:10]}")
        print(f"         {i['title'][:90]}")


def cmd_get(args):
    path = f"/api/issues/{args.identifier}"
    if args.comments:
        path += "?include=comments"
    issue = api("GET", path)
    if not issue:
        print(f"Issue {args.identifier} not found.")
        return

    assignee = issue.get("assignee")
    aname = assignee.get("name", "N/A") if assignee else "N/A"
    labels = ", ".join(l["name"] for l in issue.get("labels", []))

    print(f"{'='*60}")
    print(f"{issue['identifier']} | {issue['state']['name']} | {aname}")
    print(f"Labels: [{labels}]")
    print(f"Created: {issue.get('createdAt','')[:10]} | Updated: {issue.get('updatedAt','')[:10]} | Comments: {issue.get('commentCount',0)}")
    print(f"Title: {issue['title']}")
    print(f"{'='*60}")

    desc = issue.get("description", "") or ""
    if desc:
        # Show first 500 chars of description
        print(f"\nDescription:\n{desc[:500]}")
        if len(desc) > 500:
            print(f"... ({len(desc)} chars total)")

    if args.comments:
        comments = issue.get("comments", [])
        print(f"\n--- Comments ({len(comments)}) ---")
        for c in comments:
            author = c.get("author", {}).get("name", "Unknown")
            created = c.get("createdAt", "")[:10]
            body = (c.get("body") or "")[:300]
            print(f"\n[{created}] {author}:")
            print(f"  {body}")


def cmd_search(args):
    issues = api("GET", f"/api/issues?q={urllib.parse.quote(args.query)}&teamId={TEAM_AI}&limit=50")
    print(f"Search '{args.query}': {len(issues)} results\n")
    for i in issues[:20]:
        print(f"{i['identifier']:8s} | {i['state']['name']:12s} | {i['title'][:80]}")


def cmd_team_status(args):
    team_id = args.team or TEAM_AI
    issues = api("GET", f"/api/issues?teamId={team_id}&limit=500")
    active = [i for i in issues if i["state"]["type"] not in ("completed", "canceled", "duplicate")]
    now = datetime.now(timezone.utc)

    from collections import defaultdict
    by_person = defaultdict(list)
    unassigned = []

    for i in active:
        assignee = i.get("assignee")
        if assignee and assignee.get("name"):
            name = assignee["name"]
        else:
            labels = [l["name"] for l in i.get("labels", [])]
            if labels:
                name = labels[0]
            else:
                name = "Unassigned"
                unassigned.append(i)
                continue
        by_person[name].append(i)

    print(f"Team Status: {len(active)} active / {len(issues)} total\n")
    for person in sorted(by_person.keys()):
        items = by_person[person]
        in_progress = sum(1 for i in items if i["state"]["name"] == "In Progress")
        in_review = sum(1 for i in items if i["state"]["name"] == "In Review")
        todo = sum(1 for i in items if i["state"]["name"] == "Todo")
        print(f"  {person:25s}: {len(items):2d} active ({in_progress} IP, {in_review} IR, {todo} Todo)")

    if unassigned:
        print(f"\n  Unassigned: {len(unassigned)}")


def cmd_create(args):
    state_id = STATE_IDS["todo"]
    payload = {
        "title": args.title,
        "description": args.description or "",
        "teamId": TEAM_AI,
        "stateId": state_id,
    }

    if args.label:
        label_id = resolve_label_id(args.label)
        if label_id:
            payload["labelIds"] = [label_id]

    result = api("POST", "/api/issues", payload)
    print(f"Created: {result['identifier']} — {result['title']}")
    if "url" in result:
        print(f"URL: {result['url']}")


def cmd_update_status(args):
    # First get the issue to find its UUID
    issue = api("GET", f"/api/issues/{args.identifier}")
    if not issue:
        print(f"Issue {args.identifier} not found.")
        return

    state_id = resolve_state_id(args.state)
    result = api("PATCH", f"/api/issues/{issue['id']}", {"stateId": state_id})
    print(f"Updated {args.identifier} → {args.state}")


def cmd_add_comment(args):
    # Get issue UUID
    issue = api("GET", f"/api/issues/{args.identifier}")
    if not issue:
        print(f"Issue {args.identifier} not found.")
        return

    result = api("POST", f"/api/issues/{issue['id']}/comments", {"body": args.body})
    author = result.get("author", {}).get("name", "?")
    print(f"Comment posted on {args.identifier} by {author}")


def cmd_assign(args):
    issue = api("GET", f"/api/issues/{args.identifier}")
    if not issue:
        print(f"Issue {args.identifier} not found.")
        return
    result = api("PATCH", f"/api/issues/{issue['id']}", {"assigneeId": args.to})
    print(f"Assigned {args.identifier} → {args.to}")


def cmd_labels(args):
    labels = api("GET", "/api/labels")
    for l in sorted(labels, key=lambda x: x["name"]):
        print(f"  {l['name']:25s} | count={l.get('issueCount',0):3d} | id={l['id']}")


def cmd_teams(args):
    teams = api("GET", "/api/teams")
    for t in teams:
        members = t.get("members", [])
        print(f"  {t['key']:6s} | {t['name']:20s} | members={len(members)} | id={t['id']}")


def cmd_projects(args):
    projects = api("GET", "/api/projects")
    for p in projects:
        print(f"  {p['name']:30s} | slug={p.get('slug','')} | id={p['id']}")


def main():
    parser = argparse.ArgumentParser(description="Mobius Ticket Pilot CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list-active", help="List active issues")
    p.add_argument("--team", default=None, help="Team UUID (default: ai-team AI)")
    p.set_defaults(func=cmd_list_active)

    p = sub.add_parser("get", help="Get issue detail")
    p.add_argument("identifier", help="Issue identifier (e.g. AI-1234)")
    p.add_argument("--comments", action="store_true", help="Include comments")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("search", help="Full-text search")
    p.add_argument("query", help="Search query")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("team-status", help="Team summary")
    p.add_argument("--team", default=None, help="Team UUID")
    p.set_defaults(func=cmd_team_status)

    p = sub.add_parser("create", help="Create new issue")
    p.add_argument("title", help="Issue title")
    p.add_argument("--description", default="", help="Issue description")
    p.add_argument("--label", default=None, help="Label name (e.g. '<your label>')")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("update-status", help="Change issue state")
    p.add_argument("identifier", help="Issue identifier")
    p.add_argument("--state", required=True, help="State name (todo/in_progress/in review/done/canceled)")
    p.set_defaults(func=cmd_update_status)

    p = sub.add_parser("add-comment", help="Add a comment")
    p.add_argument("identifier", help="Issue identifier")
    p.add_argument("--body", required=True, help="Comment body")
    p.set_defaults(func=cmd_add_comment)

    p = sub.add_parser("assign", help="Assign issue")
    p.add_argument("identifier", help="Issue identifier")
    p.add_argument("--to", required=True, help="User UUID")
    p.set_defaults(func=cmd_assign)

    p = sub.add_parser("labels", help="List all labels")
    p.set_defaults(func=cmd_labels)

    p = sub.add_parser("teams", help="List all teams")
    p.set_defaults(func=cmd_teams)

    p = sub.add_parser("projects", help="List all projects")
    p.set_defaults(func=cmd_projects)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    import urllib.parse  # needed for quote in search
    main()
