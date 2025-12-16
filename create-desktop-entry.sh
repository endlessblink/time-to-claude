#!/bin/bash
# Creates a desktop entry pointing to this installation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/claude-usage-monitor.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Claude Usage Monitor
Comment=Monitor Claude API usage quotas in your system tray
Exec=$SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/icons/claude-green.svg
Terminal=false
Categories=Utility;Network;
Keywords=claude;ai;usage;monitor;quota;
StartupNotify=false
EOF

echo "Desktop entry created: $DESKTOP_FILE"

# Ask about autostart
read -p "Enable autostart on login? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"
    cp "$DESKTOP_FILE" "$AUTOSTART_DIR/"
    echo "Autostart enabled: $AUTOSTART_DIR/claude-usage-monitor.desktop"
fi

echo ""
echo "Done! You can now find 'Claude Usage Monitor' in your application menu."
