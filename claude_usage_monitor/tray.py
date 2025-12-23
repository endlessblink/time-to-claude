"""System tray icon with dynamic ring indicators."""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QAction
from PySide6.QtCore import Qt, QTimer, QRect, QPoint

from .api import ClaudeAPI, UsageData
from . import credentials


def get_5h_color(usage: float) -> QColor:
    """Get color for 5-hour usage (green -> orange -> red)."""
    if usage >= 0.90:
        return QColor("#EF4444")  # Red
    elif usage >= 0.70:
        return QColor("#F97316")  # Orange
    else:
        return QColor("#22C55E")  # Green


def get_7d_color(usage: float) -> QColor:
    """Get color for 7-day usage (cyan -> blue-purple -> deep purple)."""
    if usage >= 0.90:
        return QColor("#7C3AED")  # Deep purple
    elif usage >= 0.70:
        return QColor("#8B5CF6")  # Blue-purple
    else:
        return QColor("#06B6D4")  # Cyan


def create_ring_icon(percentage: int, color: QColor, size: int = 22) -> QIcon:
    """Create a circular ring icon with percentage number inside."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    center = size // 2
    radius = size // 2 - 2
    pen_width = 2.5

    # Draw background track (gray ring)
    bg_pen = QPen(QColor("#4B5563"), pen_width)
    bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(bg_pen)
    painter.drawEllipse(QPoint(center, center), radius, radius)

    # Draw progress arc
    if percentage > 0:
        progress_pen = QPen(color, pen_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)

        # Qt uses 1/16th of a degree, starts at 3 o'clock, goes counter-clockwise
        # We want to start at 12 o'clock (90 degrees) and go clockwise
        start_angle = 90 * 16  # 12 o'clock position
        span_angle = -int((percentage / 100) * 360 * 16)  # Negative for clockwise

        rect = QRect(center - radius, center - radius, radius * 2, radius * 2)
        painter.drawArc(rect, start_angle, span_angle)

    # Draw percentage number in center
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Sans", 7, QFont.Weight.Bold)
    painter.setFont(font)

    text = str(percentage)
    text_rect = QRect(0, 0, size, size)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

    painter.end()
    return QIcon(pixmap)


class UsageTrayIcon(QSystemTrayIcon):
    """System tray icon showing Claude 5-hour usage (primary icon)."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.api = None
        self.usage_data = None
        self.popup = None

        # Create secondary icon for 7-day usage
        self.icon_7d = QSystemTrayIcon(parent)
        self.icon_7d.setIcon(create_ring_icon(0, QColor("#6B7280")))
        self.icon_7d.setToolTip("Claude 7-Day Usage")
        self.icon_7d.activated.connect(self._on_activated)

        # Create initial icon (gray/empty state)
        self.setIcon(create_ring_icon(0, QColor("#6B7280")))
        self.setToolTip("Claude 5-Hour Usage")

        # Create context menu
        self._create_menu()

        # Initialize API if credentials exist
        if credentials.has_credentials():
            self.api = ClaudeAPI()

        # Set up refresh timer (every 5 minutes)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5 * 60 * 1000)  # 5 minutes

        # Connect click signal
        self.activated.connect(self._on_activated)

        # Show secondary icon
        self.icon_7d.show()

        # Initial refresh
        QTimer.singleShot(500, self.refresh)

    def _create_menu(self):
        """Create the context menu."""
        menu = QMenu()

        # Show popup action
        show_action = QAction("Show Usage", menu)
        show_action.triggered.connect(self._show_popup)
        menu.addAction(show_action)

        menu.addSeparator()

        # Refresh action
        refresh_action = QAction("Refresh Now", menu)
        refresh_action.triggered.connect(self.refresh)
        menu.addAction(refresh_action)

        # Open Claude.ai
        open_action = QAction("Open Claude.ai", menu)
        open_action.triggered.connect(self._open_claude)
        menu.addAction(open_action)

        # Settings
        settings_action = QAction("Settings...", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Quit
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self._menu = menu  # Keep reference

    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_popup()

    def _show_popup(self):
        """Show the usage popup window."""
        from .popup import UsagePopup

        if self.popup:
            self.popup.close()
            self.popup = None

        self.popup = UsagePopup(self.usage_data)
        self.popup.refresh_requested.connect(self.refresh)
        self.popup.settings_requested.connect(self._show_settings)

        # Position near tray icon (above the panel with extra offset)
        geometry = self.geometry()
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()

        if geometry.isValid():
            # Position well above the tray icon (extra 40px offset)
            x = geometry.x() - self.popup.width() // 2
            y = geometry.y() - self.popup.height() - 45
        else:
            # Fallback: position at cursor
            from PySide6.QtGui import QCursor
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() - self.popup.width() // 2
            y = cursor_pos.y() - self.popup.height() - 50

        # Keep on screen horizontally
        if x + self.popup.width() > screen.width():
            x = screen.width() - self.popup.width() - 10
        if x < 10:
            x = 10

        # Keep on screen vertically (don't go above screen top)
        if y < 10:
            y = 10

        self.popup.move(x, y)
        self.popup.show()
        self.popup.activateWindow()

    def _open_claude(self):
        """Open Claude.ai in browser."""
        import subprocess
        subprocess.Popen(["xdg-open", "https://claude.ai/settings/usage"])

    def _show_settings(self):
        """Show settings dialog."""
        from .settings import SettingsDialog
        dialog = SettingsDialog()
        if dialog.exec():
            # Close popup so it reopens with new theme settings
            if self.popup:
                self.popup.close()
                self.popup = None
            # Credentials may have changed, reinitialize API
            if credentials.has_credentials():
                self.api = ClaudeAPI()
                self.refresh()

    def _quit(self):
        """Quit the application."""
        self.icon_7d.hide()
        self.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def refresh(self):
        """Fetch and update usage data."""
        if not self.api:
            if credentials.has_credentials():
                self.api = ClaudeAPI()
            else:
                self._update_disconnected()
                return

        self.usage_data = self.api.fetch_usage()
        self._update_display()

        # Update popup if visible
        if self.popup and self.popup.isVisible():
            self.popup.update_data(self.usage_data)

    def _update_display(self):
        """Update tray icons based on usage data."""
        if not self.usage_data or not self.usage_data.is_connected:
            self._update_disconnected()
            return

        # Update 5-hour icon (primary)
        pct_5h = self.usage_data.short_term_percent
        color_5h = get_5h_color(self.usage_data.short_term_usage)
        self.setIcon(create_ring_icon(pct_5h, color_5h))

        # Update 7-day icon (secondary)
        pct_7d = self.usage_data.long_term_percent
        color_7d = get_7d_color(self.usage_data.long_term_usage)
        self.icon_7d.setIcon(create_ring_icon(pct_7d, color_7d))

        # Update tooltips
        reset_5h = self.usage_data.short_term_reset_str
        reset_7d = self.usage_data.long_term_reset_str
        self.setToolTip(f"5-Hour: {pct_5h}% (resets in {reset_5h})")
        self.icon_7d.setToolTip(f"7-Day: {pct_7d}% (resets in {reset_7d})")

    def _update_disconnected(self):
        """Update display for disconnected state."""
        self.setIcon(create_ring_icon(0, QColor("#6B7280")))
        self.setToolTip("Claude 5-Hour - Not connected")
        self.icon_7d.setIcon(create_ring_icon(0, QColor("#6B7280")))
        self.icon_7d.setToolTip("Claude 7-Day - Not connected")
