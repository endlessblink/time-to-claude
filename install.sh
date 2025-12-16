#!/bin/bash
# Claude Usage Monitor Installation Script

set -e

echo "Claude Usage Monitor - Installation"
echo "===================================="

# Check for required system dependencies
echo ""
echo "Checking system dependencies..."

MISSING_DEPS=""

if ! dpkg -l | grep -q python3-gi; then
    MISSING_DEPS="$MISSING_DEPS python3-gi"
fi

if ! dpkg -l | grep -qE "gir1.2-(ayatana)?appindicator3"; then
    MISSING_DEPS="$MISSING_DEPS gir1.2-ayatanaappindicator3-0.1"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo "Missing system dependencies:$MISSING_DEPS"
    echo ""
    echo "Installing system dependencies (requires sudo)..."
    sudo apt update
    sudo apt install -y python3-gi python3-gi-cairo gir1.2-ayatanaappindicator3-0.1
else
    echo "All system dependencies are installed."
fi

# Install Python package
echo ""
echo "Installing Python package..."

if command -v pipx &> /dev/null; then
    echo "Using pipx for installation..."
    pipx install . --force
else
    echo "Using pip for installation..."
    pip install --user .
fi

# Install desktop file
echo ""
echo "Installing desktop entry..."
mkdir -p ~/.local/share/applications
cp claude-usage-monitor.desktop ~/.local/share/applications/

# Install icons
echo ""
echo "Installing icons..."
mkdir -p ~/.local/share/icons/claude-usage-monitor
cp icons/*.svg ~/.local/share/icons/claude-usage-monitor/

echo ""
echo "Installation complete!"
echo ""
echo "You can now:"
echo "  1. Run 'claude-usage-monitor' from the terminal"
echo "  2. Search for 'Claude Usage Monitor' in your application menu"
echo ""
echo "On first run, you'll be prompted to enter your credentials."
echo "See the README for instructions on how to get your session key and org ID."
