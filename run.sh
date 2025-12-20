#!/bin/bash
# Claude Usage Monitor - Portable Run Script (PySide6 version)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Claude Usage Monitor${NC}"
echo "========================"

# Create virtual environment if it doesn't exist
setup_venv() {
    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
        echo "Setting up virtual environment..."

        # Remove incomplete venv if exists
        rm -rf "$VENV_DIR"

        python3 -m venv "$VENV_DIR"

        if [ ! -f "$VENV_DIR/bin/pip" ]; then
            echo -e "${RED}Failed to create virtual environment.${NC}"
            echo "Please ensure python3-venv is installed:"
            echo "  sudo apt install python3-venv"
            exit 1
        fi

        # Install dependencies
        echo "Installing Python dependencies..."
        "$VENV_DIR/bin/pip" install --quiet --upgrade pip
        "$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

        echo -e "${GREEN}Setup complete!${NC}"
        echo ""
    fi
}

# Check if PySide6 is installed, install if needed
check_deps() {
    if ! "$VENV_DIR/bin/python" -c "import PySide6" 2>/dev/null; then
        echo "Installing PySide6..."
        "$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
    fi
}

# Main
setup_venv
check_deps

# Run the application
echo "Starting Claude Usage Monitor..."
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
exec "$VENV_DIR/bin/python" -m claude_usage_monitor.main "$@"
