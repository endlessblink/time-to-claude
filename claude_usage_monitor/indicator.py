"""System tray indicator for Claude Usage Monitor."""

import gi
gi.require_version('Gtk', '3.0')

# Try Ayatana AppIndicator first (modern systems), fall back to legacy AppIndicator3
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ValueError, ImportError):
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3

from gi.repository import Gtk, GLib, Gdk
from typing import Optional
from pathlib import Path

from .api import ClaudeAPI, UsageData
from .config import ConfigManager
from .icons import DynamicIconManager
from . import credentials


class UsageIndicator:
    """System tray indicator showing Claude usage status."""

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.api: Optional[ClaudeAPI] = None
        self.usage_data: Optional[UsageData] = None
        self.refresh_timeout_id: Optional[int] = None
        self.popup: Optional[Gtk.Window] = None

        # Dynamic icon manager
        self.icon_manager = DynamicIconManager()

        # Create the indicator
        self.indicator = AppIndicator3.Indicator.new(
            "claude-usage-monitor",
            self.icon_manager.get_disconnected_icon_path(),
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Build minimal menu (required by AppIndicator)
        self.menu = self._build_menu()
        self.indicator.set_menu(self.menu)

        # Initialize API
        self._init_api()

    def _init_api(self) -> None:
        """Initialize API client."""
        if credentials.has_credentials():
            self.api = ClaudeAPI()

    def _build_menu(self) -> Gtk.Menu:
        """Build the indicator menu."""
        menu = Gtk.Menu()

        # Show popup item
        show_item = Gtk.MenuItem(label="Show Usage")
        show_item.connect("activate", self._on_show_popup)
        menu.append(show_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Refresh now
        refresh_item = Gtk.MenuItem(label="Refresh Now")
        refresh_item.connect("activate", self._on_refresh)
        menu.append(refresh_item)

        # Open Claude.ai
        open_item = Gtk.MenuItem(label="Open Claude.ai")
        open_item.connect("activate", self._on_open_claude)
        menu.append(open_item)

        # Settings
        settings_item = Gtk.MenuItem(label="Settings...")
        settings_item.connect("activate", self._on_settings)
        menu.append(settings_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Quit
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._on_quit)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def _on_show_popup(self, widget: Gtk.MenuItem) -> None:
        """Show the usage popup."""
        self._show_popup()

    def _show_popup(self) -> None:
        """Create and show the popup window."""
        from .ui.usage_popup import UsagePopup

        if self.popup:
            self.popup.destroy()

        self.popup = UsagePopup(
            usage_data=self.usage_data,
            on_refresh=self.refresh,
            on_settings=self._do_show_settings,
            on_quit=self._do_quit
        )

        # Get cursor position (near tray icon when user clicks)
        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        pointer = seat.get_pointer()
        _, cursor_x, cursor_y = pointer.get_position()

        screen = Gdk.Screen.get_default()
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        popup_width = 340
        popup_height = 280

        # Center popup horizontally on cursor, position below panel
        x = cursor_x - popup_width // 2
        y = 32  # Just below typical panel height

        # Keep on screen
        if x < 10:
            x = 10
        if x + popup_width > screen_width - 10:
            x = screen_width - popup_width - 10

        # If cursor is at bottom of screen, position above cursor
        if cursor_y > screen_height // 2:
            y = cursor_y - popup_height - 10

        self.popup.move(x, y)
        self.popup.show_all()
        self.popup.present()

    def _on_refresh(self, widget: Gtk.MenuItem) -> None:
        """Handle refresh menu item click."""
        self._init_api()
        self.refresh()

    def _on_open_claude(self, widget: Gtk.MenuItem) -> None:
        """Open Claude.ai in browser."""
        import subprocess
        subprocess.Popen(["xdg-open", "https://claude.ai/settings/usage"])

    def _on_settings(self, widget: Gtk.MenuItem) -> None:
        """Open settings dialog."""
        self._do_show_settings()

    def _do_show_settings(self) -> None:
        """Actually show settings dialog."""
        from .ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(on_save_callback=self._on_credentials_updated)
        dialog.run()
        dialog.destroy()

    def _on_credentials_updated(self) -> None:
        """Called when credentials are updated."""
        self._init_api()
        self.refresh()

    def _on_quit(self, widget: Gtk.MenuItem) -> None:
        """Handle quit menu item click."""
        self._do_quit()

    def _do_quit(self) -> None:
        """Perform quit."""
        self.stop_refresh()
        self.icon_manager.cleanup()
        Gtk.main_quit()

    def refresh(self) -> None:
        """Fetch and display current usage data."""
        if not self.api:
            self._init_api()

        if not self.api:
            self._update_disconnected("Run 'claude' to login")
            return

        GLib.idle_add(self._do_refresh)

    def _do_refresh(self) -> bool:
        """Perform the actual refresh."""
        if not self.api:
            return False

        self.usage_data = self.api.fetch_usage()
        self._update_display()

        # Update popup if visible
        if self.popup and self.popup.get_visible():
            self.popup.update(self.usage_data)

        return False

    def _update_display(self) -> None:
        """Update indicator icon and label."""
        if not self.usage_data:
            self._update_disconnected("No data")
            return

        if not self.usage_data.is_connected:
            self._update_disconnected(self.usage_data.error or "Not connected")
            return

        # Update icon with dynamic ring
        icon_path = self.icon_manager.get_icon_path(
            self.usage_data.short_term_usage,
            self.usage_data.long_term_usage
        )
        self.indicator.set_icon_full(icon_path, "Claude Usage")

        # Always show usage and time in tray label
        short_pct = self.usage_data.short_term_percent
        long_pct = self.usage_data.long_term_percent

        # Show the more concerning usage with its reset time
        if short_pct >= long_pct:
            reset_str = self.usage_data.short_term_reset_str
            self.indicator.set_label(f"{short_pct}% · {reset_str}", "")
        else:
            reset_str = self.usage_data.long_term_reset_str
            self.indicator.set_label(f"{long_pct}% · {reset_str}", "")

    def _update_disconnected(self, message: str) -> None:
        """Update display for disconnected state."""
        icon_path = self.icon_manager.get_disconnected_icon_path()
        self.indicator.set_icon_full(icon_path, "Claude Usage - Disconnected")
        self.indicator.set_label("", "")

    def start_refresh(self) -> None:
        """Start periodic refresh."""
        if self.refresh_timeout_id:
            GLib.source_remove(self.refresh_timeout_id)

        self.refresh()

        # Refresh every 5 minutes
        interval_ms = self.config.config.refresh_interval * 60 * 1000
        self.refresh_timeout_id = GLib.timeout_add(interval_ms, self._periodic_refresh)

    def _periodic_refresh(self) -> bool:
        """Called periodically to refresh."""
        self.refresh()
        return True

    def stop_refresh(self) -> None:
        """Stop periodic refresh."""
        if self.refresh_timeout_id:
            GLib.source_remove(self.refresh_timeout_id)
            self.refresh_timeout_id = None
