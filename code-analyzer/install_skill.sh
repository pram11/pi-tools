#!/bin/bash
# install_skill.sh - Code Analyzer skill deployment (Rust binary)

set -e

GLOBAL_SKILL_DIR="$HOME/.pi/skills/code-analyzer"
BIN_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building code-analyzer..."

if ! command -v cargo &> /dev/null; then
    echo "ERROR: cargo not found. Install Rust first: https://rustup.rs"
    exit 1
fi

cd "$BIN_DIR"
cargo build --release
BINARY="$BIN_DIR/target/release/code-analyzer"

if [ ! -f "$BINARY" ]; then
    echo "ERROR: Build failed - binary not found"
    exit 1
fi

mkdir -p "$GLOBAL_SKILL_DIR"

echo "Deploying binary to $GLOBAL_SKILL_DIR..."
cp "$BINARY" "$GLOBAL_SKILL_DIR/code-analyzer"
cp "$BIN_DIR/SKILL.md" "$GLOBAL_SKILL_DIR/SKILL.md"
chmod +x "$GLOBAL_SKILL_DIR/code-analyzer"

echo "Done: $GLOBAL_SKILL_DIR/code-analyzer"
echo "Binary size: $(du -h "$GLOBAL_SKILL_DIR/code-analyzer" | cut -f1)"
