#!/bin/bash
# mobius-ticket-pilot install script
# POSIX-compatible (works on bash 3.2 macOS and bash 4+ Linux)
# Usage: curl -fsSL .../install.sh | bash
#        curl -fsSL .../install.sh | bash -s -- --agent claude,codex
#        bash install.sh --agent claude

set -e

SKILL_NAME="mobius-ticket-pilot"
REPO_URL="https://github.com/RachelXiaolan/mobius-ticket-pilot"
TARBALL_URL="https://codeload.github.com/RachelXiaolan/mobius-ticket-pilot/tar.gz/refs/heads/main"
MCP_URL="https://mobius.feedmob.com/api/mcp"

# Parse --agent (comma-separated list allowed)
AGENTS=""
while [ $# -gt 0 ]; do
    case "$1" in
        --agent) AGENTS="$2"; shift 2 ;;
        --agent=*) AGENTS="${1#--agent=}"; shift ;;
        *) shift ;;
    esac
done

# Auto-detect agent if not specified
if [ -z "$AGENTS" ]; then
    if [ -d "$HOME/.claude" ]; then
        AGENTS="claude"
    elif [ -d "$HOME/.hermes" ]; then
        AGENTS="hermes"
    elif [ -d "$HOME/.codex" ]; then
        AGENTS="codex"
    elif [ -d "$HOME/.openclaw" ]; then
        AGENTS="openclaw"
    else
        AGENTS="claude"
    fi
fi

skills_dir_for() {
    case "$1" in
        hermes)   echo "$HOME/.hermes/skills/productivity" ;;
        claude)   echo "$HOME/.claude/skills" ;;
        codex)    echo "$HOME/.codex/skills" ;;
        openclaw) echo "$HOME/.openclaw/skills" ;;
        cursor)   echo ".cursor/skills" ;;
        gemini)   echo ".gemini/skills" ;;
        *)        echo "" ;;
    esac
}

# Fetch the full repo once into a temp dir (git if available, else tarball)
SRC_DIR="$(mktemp -d)"
trap 'rm -rf "$SRC_DIR"' EXIT

if command -v git >/dev/null 2>&1 && git clone --depth 1 -q "$REPO_URL" "$SRC_DIR/repo" 2>/dev/null; then
    rm -rf "$SRC_DIR/repo/.git"
else
    echo "git unavailable or clone failed, downloading tarball..."
    mkdir -p "$SRC_DIR/repo"
    curl -fsSL "$TARBALL_URL" | tar -xz -C "$SRC_DIR/repo" --strip-components 1
fi

if [ ! -f "$SRC_DIR/repo/SKILL.md" ]; then
    echo "❌ Download failed: SKILL.md not found" >&2
    exit 1
fi

INSTALLED=""
OLD_IFS="$IFS"; IFS=","
for AGENT in $AGENTS; do
    IFS="$OLD_IFS"
    SKILLS_DIR="$(skills_dir_for "$AGENT")"
    if [ -z "$SKILLS_DIR" ]; then
        echo "⚠️  Unknown agent '$AGENT' — skipped (valid: claude codex hermes openclaw cursor gemini)"
        continue
    fi
    TARGET="$SKILLS_DIR/$SKILL_NAME"
    echo "Installing $SKILL_NAME for $AGENT → $TARGET"
    mkdir -p "$SKILLS_DIR"
    rm -rf "$TARGET"
    mkdir -p "$TARGET"
    cp -R "$SRC_DIR/repo/SKILL.md" "$SRC_DIR/repo/references" "$SRC_DIR/repo/scripts" "$TARGET/"
    for f in README.md README_EN.md CHANGELOG.md LICENSE; do
        [ -f "$SRC_DIR/repo/$f" ] && cp "$SRC_DIR/repo/$f" "$TARGET/"
    done
    chmod +x "$TARGET"/scripts/*.py 2>/dev/null || true
    INSTALLED="$INSTALLED $TARGET"
done
IFS="$OLD_IFS"

if [ -z "$INSTALLED" ]; then
    echo "❌ Nothing installed." >&2
    exit 1
fi

echo ""
echo "✅ $SKILL_NAME installed to:$INSTALLED"
echo ""
echo "Next step — connect Mobius (recommended: MCP + OAuth, no token needed):"
echo "  Claude Code:  claude mcp add --transport http --scope user mobius $MCP_URL"
echo "                then run /mcp in a session → mobius → Authenticate"
echo "  Other clients: add $MCP_URL as an HTTP MCP server and sign in"
echo ""
echo "Fallback (REST + scripts):"
echo "  export MOBIUS_API_KEY=\"mob_your_token_here\""
echo "  python3 <skill dir>/scripts/mobius_cli.py teams"
