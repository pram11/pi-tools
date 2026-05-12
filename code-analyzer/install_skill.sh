#!/bin/bash
# install_skill.sh - Pi Code Analyst skill global deployment

LOCAL_SKILL_DIR="./.pi/skills/code-analyzer"
GLOBAL_SKILL_DIR="$HOME/.pi/skills/code-analyzer"

echo "Installing code-analyzer skill..."

if [ ! -d "$LOCAL_SKILL_DIR" ]; then
    echo "ERROR: Local skill dir not found: $LOCAL_SKILL_DIR"
    exit 1
fi

mkdir -p "$HOME/.pi/skills"

if [ -d "$GLOBAL_SKILL_DIR" ]; then
    echo "Updating existing global skill..."
    rm -rf "$GLOBAL_SKILL_DIR"
fi

cp -r "$LOCAL_SKILL_DIR" "$GLOBAL_SKILL_DIR"
chmod +x "$GLOBAL_SKILL_DIR/scripts/"*.py 2>/dev/null || true

if [ -f "$GLOBAL_SKILL_DIR/requirements.txt" ]; then
    echo "Installing dependencies in venv..."
    python3 -m venv "$GLOBAL_SKILL_DIR/.venv" 2>/dev/null
    "$GLOBAL_SKILL_DIR/.venv/bin/pip" install -r "$GLOBAL_SKILL_DIR/requirements.txt" --quiet
fi

echo "Done: $GLOBAL_SKILL_DIR"
