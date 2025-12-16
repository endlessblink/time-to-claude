"""Configuration management for Claude Usage Monitor."""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    refresh_interval: int = 5  # minutes
    display_mode: str = "icon_and_text"  # icon_only, text_only, icon_and_text
    show_notifications: bool = True
    warning_threshold: int = 50  # percentage to show orange
    critical_threshold: int = 80  # percentage to show red
    autostart: bool = False


class ConfigManager:
    """Manages loading and saving configuration."""

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "claude-usage-monitor"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load()

    def _load(self) -> Config:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    return Config(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return Config()

    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(asdict(self.config), f, indent=2)

    def get_icon_path(self) -> Path:
        """Get path to icons directory."""
        # Check installed location first
        installed_path = Path("/usr/share/icons/claude-usage-monitor")
        if installed_path.exists():
            return installed_path

        # Check local share
        local_path = Path.home() / ".local/share/icons/claude-usage-monitor"
        if local_path.exists():
            return local_path

        # Fall back to package directory
        package_dir = Path(__file__).parent.parent / "icons"
        if package_dir.exists():
            return package_dir

        # Try relative to script
        return Path(__file__).parent.parent / "icons"

    def setup_autostart(self, enable: bool) -> None:
        """Configure autostart on login."""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_file = autostart_dir / "claude-usage-monitor.desktop"

        if enable:
            autostart_dir.mkdir(parents=True, exist_ok=True)
            desktop_entry = """[Desktop Entry]
Type=Application
Name=Claude Usage Monitor
Comment=Monitor Claude API usage quotas
Exec=claude-usage-monitor
Icon=claude-usage-monitor
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""
            with open(autostart_file, "w") as f:
                f.write(desktop_entry)
        else:
            if autostart_file.exists():
                autostart_file.unlink()

        self.config.autostart = enable
        self.save()
