#!/bin/bash
# mobius-ticket-pilot install script
# POSIX-compatible (works on bash 3.2 macOS and bash 4+ Linux)
# Usage: curl -fsSL .../install.sh | bash
#        bash install.sh --agent claude

set -e

SKILL_NAME="mobius-ticket-pilot"
REPO_URL="https://github.com/RachelXiaolan/mobius-ticket-pilot"

# Detect agent from --agent flag or auto-detect
AGENT=""
while [ $# -gt 0 ]; do
    case "$1" in
        --agent) AGENT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Auto-detect agent if not specified
if [ -z "$AGENT" ]; then
    if [ -d "$HOME/.hermes" ]; then
        AGENT="hermes"
    elif [ -d "$HOME/.claude" ]; then
        AGENT="claude"
    elif [ -d "$HOME/.codex" ]; then
        AGENT="codex"
    elif [ -d "$HOME/.openclaw" ]; then
        AGENT="openclaw"
    else
        AGENT="hermes"
    fi
fi

# Map agent to skills directory
case "$AGENT" in
    hermes)   SKILLS_DIR="$HOME/.hermes/skills/productivity" ;;
    claude)   SKILLS_DIR="$HOME/.claude/skills" ;;
    codex)    SKILLS_DIR="$HOME/.codex/skills" ;;
    openclaw) SKILLS_DIR="$HOME/.openclaw/skills" ;;
    cursor)   SKILLS_DIR=".cursor/skills" ;;
    gemini)   SKILLS_DIR=".gemini/skills" ;;
    *)        SKILLS_DIR="$HOME/.hermes/skills/productivity" ;;
esac

TARGET="$SKILLS_DIR/$SKILL_NAME"

echo "Installing $SKILL_NAME for agent: $AGENT"
echo "Target: $TARGET"

mkdir -p "$SKILLS_DIR"

# If already exists, update
if [ -d "$TARGET" ]; then
    echo "Updating existing installation..."
    rm -rf "$TARGET"
fi

# Clone or copy
if command -v git >/dev/null 2>&1; then
    git clone --depth 1 "$REPO_URL" "$TARGET" 2>/dev/null || {
        echo "git clone failed, trying curl..."
        mkdir -p "$TARGET"
        curl -fsSL "$REPO_URL/raw/main/SKILL.md" -o "$TARGET/SKILL.md"
        mkdir -p "$TARGET/scripts" "$TARGET/references"
        curl -fsSL "$REPO_URL/raw/main/scripts/mobius_cli.py" -o "$TARGET/scripts/mobius_cli.py"
        curl -fsSL "$REPO_URL/raw/main/references/onboarding-settings.md" -o "$TARGET/references/onboarding-settings.md"
        curl -fsSL "$REPO_URL/raw/main/references/state-model.md" -o "$TARGET/references/state-model.md"
    }
    # Remove .git from skill dir
    rm -rf "$TARGET/.git"
else
    echo "git not found, using curl..."
    mkdir -p "$TARGET/scripts" "$TARGET/references"
    curl -fsSL "$REPO_URL/raw/main/SKILL.md" -o "$TARGET/SKILL.md"
    curl -fsSL "$REPO_URL/raw/main/scripts/mobius_cli.py" -o "$TARGET/scripts/mobius_cli.py"
    curl -fsSL "$REPO_URL/raw/main/references/onboarding-settings.md" -o "$TARGET/references/onboarding-settings.md"
    curl -fsSL "$REPO_URL/raw/main/references/state-model.md" -o "$TARGET/references/state-model.md"
fi

echo ""
echo "✅ $SKILL_NAME installed to $TARGET"
echo ""
echo "Next steps:"
echo "  1. Set your Mobius API key:"
echo "     export MOBIUS_API_KEY=\"mob_your_token_here\""
echo "  2. Test the connection:"
echo "     python3 $TARGET/scripts/mobius_cli.py teams"
