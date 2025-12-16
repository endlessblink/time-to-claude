"""Usage popup window with dual-ring progress indicator."""

import math
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QIcon, QPainterPath
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize

from .api import UsageData
from .tray import get_5h_color, get_7d_color
from . import credentials


class DualRingWidget(QWidget):
    """Widget displaying dual concentric progress rings with percentage."""

    def __init__(self, dark_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self.outer_progress = 0.0  # 5-hour (0.0 to 1.0)
        self.inner_progress = 0.0  # 7-day (0.0 to 1.0)
        self.dark_mode = dark_mode

    def set_progress(self, outer: float, inner: float):
        """Set progress values (0.0 to 1.0)."""
        self.outer_progress = max(0.0, min(1.0, outer))
        self.inner_progress = max(0.0, min(1.0, inner))
        self.update()

    def paintEvent(self, event):
        """Draw the dual concentric rings."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPoint(width // 2, height // 2)

        # Ring parameters
        outer_radius = 75
        inner_radius = 55
        outer_width = 12
        inner_width = 10

        # Background track color
        track_color = QColor("#374151") if self.dark_mode else QColor("#E5E7EB")

        # Draw outer track (5-hour background)
        self._draw_ring(painter, center, outer_radius, outer_width, track_color, 1.0)

        # Draw inner track (7-day background)
        self._draw_ring(painter, center, inner_radius, inner_width, track_color, 1.0)

        # Draw outer progress (5-hour)
        if self.outer_progress > 0.001:
            outer_color = get_5h_color(self.outer_progress)
            self._draw_ring(painter, center, outer_radius, outer_width, outer_color, self.outer_progress)

        # Draw inner progress (7-day)
        if self.inner_progress > 0.001:
            inner_color = get_7d_color(self.inner_progress)
            self._draw_ring(painter, center, inner_radius, inner_width, inner_color, self.inner_progress)

        # Draw percentage text in center
        outer_pct = int(self.outer_progress * 100)
        text_color = QColor("#F9FAFB") if self.dark_mode else QColor("#1F2937")
        painter.setPen(text_color)

        # Large percentage number
        font = QFont("Sans", 32, QFont.Weight.Bold)
        painter.setFont(font)
        text = f"{outer_pct}%"
        text_rect = QRect(0, height // 2 - 25, width, 40)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        # "Used" label below
        font_small = QFont("Sans", 11)
        painter.setFont(font_small)
        label_color = QColor("#9CA3AF") if self.dark_mode else QColor("#6B7280")
        painter.setPen(label_color)
        used_rect = QRect(0, height // 2 + 15, width, 20)
        painter.drawText(used_rect, Qt.AlignmentFlag.AlignCenter, "Used")

        painter.end()

    def _draw_ring(self, painter: QPainter, center: QPoint, radius: int,
                   width: int, color: QColor, progress: float):
        """Draw a ring arc."""
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        rect = QRect(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2
        )

        if progress >= 0.999:
            # Full circle
            painter.drawEllipse(rect)
        else:
            # Partial arc
            start_angle = 90 * 16  # Start at 12 o'clock
            span_angle = -int(progress * 360 * 16)  # Clockwise
            painter.drawArc(rect, start_angle, span_angle)


class TimerRow(QWidget):
    """A row showing period, time remaining, and reset time."""

    def __init__(self, is_7day: bool = False, dark_mode: bool = False, parent=None):
        super().__init__(parent)
        self.is_7day = is_7day
        self.dark_mode = dark_mode

        # Colors based on theme
        text_color = "#E5E7EB" if dark_mode else "#374151"
        icon_color = "#6B7280" if dark_mode else "#9CA3AF"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(0)

        # Period indicator (5h or 7d)
        self.period_frame = QFrame()
        self.period_frame.setMinimumWidth(65)
        self.period_frame.setFixedHeight(28)
        period_layout = QHBoxLayout(self.period_frame)
        period_layout.setContentsMargins(10, 4, 10, 4)
        period_layout.setSpacing(6)

        # Period icon (clock or calendar)
        self.period_icon = QLabel()
        self.period_icon.setStyleSheet(f"color: {icon_color}; font-size: 14px;")
        if is_7day:
            self.period_icon.setText("\U0001F4C5")  # Calendar emoji
            bg_color = "#4C1D95" if dark_mode else "#EDE9FE"
            self.period_frame.setStyleSheet(f"background-color: {bg_color}; border-radius: 6px;")
        else:
            self.period_icon.setText("\U0001F551")  # Clock emoji
            bg_color = "#1E3A5F" if dark_mode else "#DBEAFE"
            self.period_frame.setStyleSheet(f"background-color: {bg_color}; border-radius: 6px;")
        period_layout.addWidget(self.period_icon)

        self.period_label = QLabel("7d" if is_7day else "5h")
        self.period_label.setStyleSheet(f"color: {text_color}; font-weight: 500; font-size: 13px;")
        period_layout.addWidget(self.period_label)

        layout.addWidget(self.period_frame)
        layout.addStretch()

        # Time remaining
        self.remaining_frame = QFrame()
        remaining_layout = QHBoxLayout(self.remaining_frame)
        remaining_layout.setContentsMargins(0, 0, 0, 0)
        remaining_layout.setSpacing(6)

        self.hourglass_icon = QLabel("\u29D6")  # Hourglass
        self.hourglass_icon.setStyleSheet(f"color: {icon_color}; font-size: 14px;")
        remaining_layout.addWidget(self.hourglass_icon)

        self.remaining_label = QLabel("--")
        self.remaining_label.setStyleSheet(f"color: {text_color}; font-weight: 500; font-size: 13px;")
        remaining_layout.addWidget(self.remaining_label)

        layout.addWidget(self.remaining_frame)
        layout.addStretch()

        # Reset time
        self.reset_frame = QFrame()
        reset_layout = QHBoxLayout(self.reset_frame)
        reset_layout.setContentsMargins(0, 0, 0, 0)
        reset_layout.setSpacing(6)

        self.clock_icon = QLabel("\U0001F552")  # Clock 3 o'clock
        self.clock_icon.setStyleSheet(f"color: {icon_color}; font-size: 14px;")
        reset_layout.addWidget(self.clock_icon)

        self.reset_label = QLabel("--:--")
        self.reset_label.setStyleSheet(f"color: {text_color}; font-weight: 500; font-size: 13px;")
        reset_layout.addWidget(self.reset_label)

        layout.addWidget(self.reset_frame)

    def set_data(self, remaining: str, reset_time: datetime = None):
        """Update the row with new data."""
        self.remaining_label.setText(remaining)

        if reset_time:
            if self.is_7day:
                # Show date and time for 7-day
                self.reset_label.setText(reset_time.strftime("%m/%d, %I %p"))
            else:
                # Show just time for 5-hour
                self.reset_label.setText(reset_time.strftime("%H:%M"))
        else:
            self.reset_label.setText("--:--")


class UsagePopup(QWidget):
    """Popup window showing detailed usage information."""

    refresh_requested = Signal()
    settings_requested = Signal()

    def __init__(self, usage_data: UsageData = None, parent=None):
        super().__init__(parent)

        self.dark_mode = credentials.is_dark_mode()

        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(340, 340)

        # Theme colors
        if self.dark_mode:
            bg_color = "#1F2937"
            border_color = "#374151"
        else:
            bg_color = "#FFFFFF"
            border_color = "#E5E7EB"

        # Main container with styling
        self.container = QFrame(self)
        self.container.setGeometry(5, 5, 330, 330)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 16px;
                border: 1px solid {border_color};
            }}
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        # Layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 12, 8)

        # Claude icon placeholder
        icon_label = QLabel()
        icon_label.setFixedSize(28, 28)
        icon_label.setStyleSheet("""
            background-color: #EA580C;
            border-radius: 6px;
            color: white;
            font-weight: bold;
            font-size: 14px;
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setText("C")
        header_layout.addWidget(icon_label)

        # Theme-specific colors
        title_color = "#F9FAFB" if self.dark_mode else "#1F2937"
        btn_color = "#9CA3AF" if self.dark_mode else "#6B7280"
        btn_hover_bg = "#374151" if self.dark_mode else "#F3F4F6"
        btn_hover_color = "#F9FAFB" if self.dark_mode else "#1F2937"

        title = QLabel("Claude Usage")
        title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {title_color}; margin-left: 8px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("\u21BB")  # Refresh symbol
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                color: {btn_color};
            }}
            QPushButton:hover {{
                background-color: {btn_hover_bg};
                color: {btn_hover_color};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Menu button
        menu_btn = QPushButton("\u22EF")  # Three dots
        menu_btn.setFixedSize(28, 28)
        menu_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                color: {btn_color};
            }}
            QPushButton:hover {{
                background-color: {btn_hover_bg};
                color: {btn_hover_color};
            }}
        """)
        menu_btn.clicked.connect(self._show_menu)
        header_layout.addWidget(menu_btn)

        # Close button
        close_btn = QPushButton("\u2715")  # X symbol
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                color: {btn_color};
            }}
            QPushButton:hover {{
                background-color: #EF4444;
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        # Dual ring widget
        self.ring_widget = DualRingWidget(dark_mode=self.dark_mode)
        ring_container = QWidget()
        ring_layout = QHBoxLayout(ring_container)
        ring_layout.setContentsMargins(0, 0, 0, 0)
        ring_layout.addStretch()
        ring_layout.addWidget(self.ring_widget)
        ring_layout.addStretch()
        layout.addWidget(ring_container)

        layout.addStretch()

        # Separator colors
        sep_color = "#374151" if self.dark_mode else "#E5E7EB"
        sep2_color = "#2D3748" if self.dark_mode else "#F3F4F6"

        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {sep_color}; margin: 0 16px;")
        layout.addWidget(separator)

        # Timer rows
        self.row_5h = TimerRow(is_7day=False, dark_mode=self.dark_mode)
        layout.addWidget(self.row_5h)

        separator2 = QFrame()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet(f"background-color: {sep2_color}; margin: 0 16px;")
        layout.addWidget(separator2)

        self.row_7d = TimerRow(is_7day=True, dark_mode=self.dark_mode)
        layout.addWidget(self.row_7d)

        # Bottom padding
        bottom_pad = QWidget()
        bottom_pad.setFixedHeight(8)
        layout.addWidget(bottom_pad)

        # Update with initial data
        if usage_data:
            self.update_data(usage_data)

    def update_data(self, usage_data: UsageData):
        """Update the popup with new usage data."""
        if not usage_data or not usage_data.is_connected:
            self.ring_widget.set_progress(0, 0)
            self.row_5h.set_data("--", None)
            self.row_7d.set_data("--", None)
            return

        # Update ring
        self.ring_widget.set_progress(
            usage_data.short_term_usage,
            usage_data.long_term_usage
        )

        # Update timer rows
        self.row_5h.set_data(
            usage_data.short_term_reset_str,
            usage_data.short_term_reset
        )
        self.row_7d.set_data(
            usage_data.long_term_reset_str,
            usage_data.long_term_reset
        )

    def _show_menu(self):
        """Show options menu."""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)

        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self.settings_requested.emit)

        open_action = menu.addAction("Open Claude.ai")
        open_action.triggered.connect(self._open_claude)

        menu.exec(self.mapToGlobal(QPoint(self.width() - 50, 45)))

    def _open_claude(self):
        """Open Claude.ai in browser."""
        import subprocess
        subprocess.Popen(["xdg-open", "https://claude.ai/settings/usage"])
        self.close()

    def keyPressEvent(self, event):
        """Close on Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Close if clicking outside the container."""
        if not self.container.geometry().contains(event.pos()):
            self.close()
        super().mousePressEvent(event)
