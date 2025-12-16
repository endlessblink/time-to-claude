#!/usr/bin/env python3
"""Claude Usage Monitor - PySide6 Main Entry Point."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

from .tray import UsageTrayIcon
from .api import ClaudeAPI
from . import credentials


def main():
    """Main entry point."""
    print("Starting Claude Usage Monitor (PySide6)...")

    app = QApplication(sys.argv)
    app.setApplicationName("Claude Usage Monitor")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    # Check for credentials
    if credentials.has_credentials():
        creds = credentials.get_credentials()
        print(f"Found credentials (source: {creds.source})")
    else:
        print("No credentials found. Use Settings to configure.")

    # Create tray icon
    tray = UsageTrayIcon()
    tray.show()

    print("Running in system tray. Click the icon for menu.")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
