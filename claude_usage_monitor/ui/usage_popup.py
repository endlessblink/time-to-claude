"""Usage popup window with circular progress indicators."""

import math
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
import cairo
from typing import Optional, Callable

from ..api import UsageData
from ..icons import get_color_for_usage


class CircularProgress(Gtk.DrawingArea):
    """A circular progress indicator with percentage in center."""

    def __init__(self, size: int = 120, stroke_width: int = 12, is_long_term: bool = False):
        super().__init__()
        self.size = size
        self.stroke_width = stroke_width
        self.is_long_term = is_long_term
        self.progress = 0.0
        self.set_size_request(size, size)
        self.connect("draw", self._on_draw)

    def set_progress(self, progress: float):
        """Set progress value (0.0 to 1.0)."""
        self.progress = min(max(progress, 0.0), 1.0)
        self.queue_draw()

    def _on_draw(self, widget, cr: cairo.Context):
        """Draw the circular progress with percentage in center."""
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        cx, cy = width / 2, height / 2
        radius = (min(width, height) - self.stroke_width) / 2 - 2

        # Background track - full circle with subtle color
        cr.set_line_width(self.stroke_width)
        cr.set_source_rgba(0.25, 0.28, 0.32, 0.8)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.stroke()

        # Progress arc with rounded ends
        if self.progress > 0.001:
            color_hex = get_color_for_usage(self.progress, self.is_long_term)
            r, g, b = self._hex_to_rgb(color_hex)

            # Add slight glow effect
            cr.set_source_rgba(r, g, b, 0.3)
            cr.set_line_width(self.stroke_width + 4)
            start_angle = -math.pi / 2
            end_angle = start_angle + (2 * math.pi * self.progress)
            cr.arc(cx, cy, radius, start_angle, end_angle)
            cr.stroke()

            # Main progress arc
            cr.set_source_rgb(r, g, b)
            cr.set_line_width(self.stroke_width)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.arc(cx, cy, radius, start_angle, end_angle)
            cr.stroke()

        # Draw percentage text in center - large and bold
        pct = int(self.progress * 100)
        cr.set_source_rgb(1, 1, 1)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

        # Main percentage number
        cr.set_font_size(28)
        text = f"{pct}"
        extents = cr.text_extents(text)
        text_x = cx - extents.width / 2 - 6
        text_y = cy + extents.height / 2 - 2
        cr.move_to(text_x, text_y)
        cr.show_text(text)

        # Smaller % sign
        cr.set_font_size(14)
        cr.move_to(text_x + extents.width + 2, text_y)
        cr.show_text("%")

    def _hex_to_rgb(self, hex_color: str):
        """Convert hex color to RGB tuple (0-1 range)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))


class UsagePopup(Gtk.Window):
    """Popup window showing detailed usage information."""

    def __init__(self, usage_data: Optional[UsageData] = None,
                 on_refresh: Optional[Callable] = None,
                 on_settings: Optional[Callable] = None,
                 on_quit: Optional[Callable] = None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.on_refresh = on_refresh
        self.on_settings = on_settings
        self.on_quit = on_quit

        self.set_title("Claude Usage")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        # Apply styling
        self._apply_styling()

        # Event box for the whole window to handle clicks
        event_box = Gtk.EventBox()
        event_box.connect("button-press-event", self._on_click_outside)
        self.add(event_box)

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.get_style_context().add_class("popup-window")
        event_box.add(self.main_box)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.get_style_context().add_class("popup-header")
        header.set_margin_start(20)
        header.set_margin_end(16)
        header.set_margin_top(16)
        header.set_margin_bottom(8)

        title = Gtk.Label(label="Claude Usage")
        title.get_style_context().add_class("popup-title")
        title.set_halign(Gtk.Align.START)
        header.pack_start(title, True, True, 0)

        # Refresh button
        refresh_btn = Gtk.Button(label="⟳")
        refresh_btn.get_style_context().add_class("header-btn")
        refresh_btn.set_tooltip_text("Refresh")
        refresh_btn.connect("clicked", self._on_refresh_clicked)
        header.pack_end(refresh_btn, False, False, 4)

        # Close button
        close_btn = Gtk.Button(label="×")
        close_btn.get_style_context().add_class("close-btn")
        close_btn.set_tooltip_text("Close")
        close_btn.connect("clicked", lambda w: self.destroy())
        header.pack_end(close_btn, False, False, 0)

        self.main_box.pack_start(header, False, False, 0)

        # Separator line
        sep = Gtk.Box()
        sep.get_style_context().add_class("separator-line")
        sep.set_size_request(-1, 1)
        self.main_box.pack_start(sep, False, False, 0)

        # Usage content area
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        self.content_box.set_margin_start(30)
        self.content_box.set_margin_end(30)
        self.content_box.set_margin_top(24)
        self.content_box.set_margin_bottom(24)
        self.content_box.set_halign(Gtk.Align.CENTER)
        self.main_box.pack_start(self.content_box, True, True, 0)

        # 5-Hour Usage Card
        self.short_term_card = self._create_usage_card("5-Hour Limit", False)
        self.content_box.pack_start(self.short_term_card, False, False, 0)

        # 7-Day Usage Card
        self.long_term_card = self._create_usage_card("7-Day Limit", True)
        self.content_box.pack_start(self.long_term_card, False, False, 0)

        # Error display (hidden by default)
        self.error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.error_box.set_margin_start(30)
        self.error_box.set_margin_end(30)
        self.error_box.set_margin_top(40)
        self.error_box.set_margin_bottom(40)
        self.error_box.set_halign(Gtk.Align.CENTER)
        self.error_box.set_no_show_all(True)

        error_icon = Gtk.Label(label="⚠")
        error_icon.get_style_context().add_class("error-icon")
        self.error_box.pack_start(error_icon, False, False, 0)

        self.error_label = Gtk.Label(label="")
        self.error_label.get_style_context().add_class("error-text")
        self.error_label.set_line_wrap(True)
        self.error_label.set_max_width_chars(30)
        self.error_box.pack_start(self.error_label, False, False, 0)

        self.main_box.pack_start(self.error_box, True, True, 0)

        # Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        footer.set_margin_start(20)
        footer.set_margin_end(20)
        footer.set_margin_bottom(16)
        footer.set_halign(Gtk.Align.CENTER)

        open_btn = Gtk.Button(label="Open Claude.ai")
        open_btn.get_style_context().add_class("footer-btn")
        open_btn.connect("clicked", self._on_open_claude)
        footer.pack_start(open_btn, False, False, 0)

        sep_label = Gtk.Label(label="•")
        sep_label.get_style_context().add_class("footer-sep")
        footer.pack_start(sep_label, False, False, 0)

        settings_btn = Gtk.Button(label="Settings")
        settings_btn.get_style_context().add_class("footer-btn")
        settings_btn.connect("clicked", self._on_settings_clicked)
        footer.pack_start(settings_btn, False, False, 0)

        self.main_box.pack_start(footer, False, False, 0)

        # Update with initial data
        if usage_data:
            self.update(usage_data)

        self.show_all()

        # Close on Escape key
        self.connect("key-press-event", self._on_key_press)

    def _apply_styling(self):
        """Apply CSS styling to the popup."""
        css = b"""
        .popup-window {
            background-color: #111827;
            border-radius: 16px;
            border: 1px solid #374151;
        }
        .popup-title {
            font-size: 16px;
            font-weight: 600;
            color: #F9FAFB;
            letter-spacing: 0.3px;
        }
        .header-btn {
            background: transparent;
            border: none;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 18px;
            color: #9CA3AF;
            min-width: 32px;
            min-height: 32px;
        }
        .header-btn:hover {
            background-color: #374151;
            color: #F9FAFB;
        }
        .close-btn {
            background: transparent;
            border: none;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 20px;
            font-weight: 300;
            color: #9CA3AF;
            min-width: 32px;
            min-height: 32px;
        }
        .close-btn:hover {
            background-color: #EF4444;
            color: #FFFFFF;
        }
        .separator-line {
            background-color: #374151;
            margin-left: 16px;
            margin-right: 16px;
        }
        .card-title {
            font-size: 11px;
            font-weight: 600;
            color: #6B7280;
            letter-spacing: 0.5px;
        }
        .reset-time {
            font-size: 15px;
            font-weight: 600;
            color: #E5E7EB;
        }
        .reset-label {
            font-size: 11px;
            color: #6B7280;
        }
        .footer-btn {
            background: transparent;
            border: none;
            padding: 6px 12px;
            font-size: 12px;
            color: #60A5FA;
            border-radius: 6px;
        }
        .footer-btn:hover {
            background-color: rgba(96, 165, 250, 0.1);
            color: #93C5FD;
        }
        .footer-sep {
            color: #4B5563;
            font-size: 10px;
        }
        .error-icon {
            font-size: 32px;
            color: #F87171;
        }
        .error-text {
            font-size: 13px;
            color: #F87171;
            text-align: center;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _create_usage_card(self, title: str, is_long_term: bool) -> Gtk.Box:
        """Create a usage card with circular progress."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_halign(Gtk.Align.CENTER)

        # Title at top (uppercase)
        title_label = Gtk.Label(label=title.upper())
        title_label.get_style_context().add_class("card-title")
        card.pack_start(title_label, False, False, 0)

        # Circular progress - larger size
        progress = CircularProgress(size=110, stroke_width=10, is_long_term=is_long_term)
        card.pack_start(progress, False, False, 10)

        if is_long_term:
            self.long_term_progress = progress
        else:
            self.short_term_progress = progress

        # Reset time
        reset_time = Gtk.Label(label="--")
        reset_time.get_style_context().add_class("reset-time")
        card.pack_start(reset_time, False, False, 0)

        if is_long_term:
            self.long_term_reset = reset_time
        else:
            self.short_term_reset = reset_time

        # "until reset" label
        reset_label = Gtk.Label(label="until reset")
        reset_label.get_style_context().add_class("reset-label")
        card.pack_start(reset_label, False, False, 0)

        return card

    def update(self, usage_data: UsageData):
        """Update the popup with new usage data."""
        if not usage_data.is_connected:
            self.content_box.hide()
            self.error_label.set_text(usage_data.error or "Not connected")
            self.error_box.show_all()
            return

        self.error_box.hide()
        self.content_box.show_all()

        # Update 5-hour usage
        self.short_term_progress.set_progress(usage_data.short_term_usage)
        self.short_term_reset.set_text(usage_data.short_term_reset_str)

        # Update 7-day usage
        self.long_term_progress.set_progress(usage_data.long_term_usage)
        self.long_term_reset.set_text(usage_data.long_term_reset_str)

    def _on_click_outside(self, widget, event):
        """Close on click outside content."""
        return False

    def _on_key_press(self, widget, event):
        """Handle key press - close on Escape."""
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def _on_refresh_clicked(self, widget):
        """Handle refresh button click."""
        if self.on_refresh:
            self.on_refresh()

    def _on_settings_clicked(self, widget):
        """Handle settings button."""
        self.destroy()
        if self.on_settings:
            self.on_settings()

    def _on_open_claude(self, widget):
        """Open Claude.ai in browser."""
        import subprocess
        subprocess.Popen(["xdg-open", "https://claude.ai/settings/usage"])
