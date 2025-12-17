#!/bin/bash
# Claude Usage Monitor - Startup Hook for Claude Code
# This script is called by Claude Code on session start

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if already running
if pgrep -f "claude_usage_monitor.main" > /dev/null 2>&1; then
    exit 0
fi

# Start in background, detached from terminal
nohup "$SCRIPT_DIR/run.sh" > /dev/null 2>&1 &

exit 0
