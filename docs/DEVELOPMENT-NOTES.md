# Development Notes

## Issues Solved During Development

### 1. GTK vs Qt Decision

**Problem**: Initial GTK/AppIndicator implementation had issues:
- CSS `text-transform` property not supported in GTK3
- AppIndicator icons are static (can't easily show dynamic percentages)
- Dark theme styling was difficult
- Popup positioning was unreliable

**Solution**: Switched to PySide6 (Qt6) because:
- KDE Plasma 6 is Qt-based - native integration
- QPainter allows dynamic icon generation
- Better control over popup windows
- Easier theming with stylesheets

### 2. Dynamic Tray Icons with Ring Progress

**Problem**: System tray icons are typically static images. We needed icons that show:
- A circular progress ring
- The percentage number inside
- Color changes based on usage level

**Solution**: Generate icons at runtime using QPainter:
```python
def create_ring_icon(percentage: int, color: QColor, size: int = 22) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)

    # Draw background track (gray ring)
    painter.drawEllipse(...)

    # Draw progress arc
    start_angle = 90 * 16  # 12 o'clock
    span_angle = -int((percentage / 100) * 360 * 16)  # Clockwise
    painter.drawArc(rect, start_angle, span_angle)

    # Draw percentage number
    painter.drawText(text_rect, Qt.AlignCenter, str(percentage))
```

### 3. Two Tray Icons (5-hour and 7-day)

**Problem**: Original Usage4Claude shows two separate icons in the macOS menu bar. Qt's QSystemTrayIcon only creates one icon per instance.

**Solution**: Create two QSystemTrayIcon instances:
```python
class UsageTrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        # Primary icon (5-hour)
        self.setIcon(create_ring_icon(0, QColor("#6B7280")))

        # Secondary icon (7-day)
        self.icon_7d = QSystemTrayIcon()
        self.icon_7d.setIcon(create_ring_icon(0, QColor("#6B7280")))
        self.icon_7d.show()
```

### 4. Popup Positioning

**Problem**: Popup appeared below the tray icons, covering them. Also, on some systems `geometry()` returns invalid values.

**Solution**: Position popup above the tray with offset, with fallback to cursor position:
```python
if geometry.isValid():
    x = geometry.x() - self.popup.width() // 2
    y = geometry.y() - self.popup.height() - 45  # Above with offset
else:
    cursor_pos = QCursor.pos()
    x = cursor_pos.x() - self.popup.width() // 2
    y = cursor_pos.y() - self.popup.height() - 50
```

### 5. Popup Closes When Taking Screenshots

**Problem**: Using `Qt.WindowType.Popup` causes the window to close when it loses focus - including when activating screenshot tools.

**Solution**: Use `Qt.WindowType.Tool` instead with `WindowStaysOnTopHint`:
```python
self.setWindowFlags(
    Qt.WindowType.Tool |
    Qt.WindowType.FramelessWindowHint |
    Qt.WindowType.WindowStaysOnTopHint |
    Qt.WindowType.NoDropShadowWindowHint
)
```

Added manual close methods:
- X button in header
- Escape key
- Click outside popup

### 6. Timer Labels Getting Cut Off

**Problem**: "5h" and "7d" period labels were being truncated, showing as "5i" and "7i".

**Solution**: Increased the period frame width and padding:
```python
self.period_frame.setMinimumWidth(65)  # Was 50
self.period_frame.setFixedHeight(28)
period_layout.setContentsMargins(10, 4, 10, 4)  # More horizontal padding
```

### 7. Dark Mode Support

**Problem**: User wanted dark mode option for the popup.

**Solution**: Added dark mode toggle in settings, stored in `settings.json`:
```python
# credentials.py
def is_dark_mode() -> bool:
    return get_settings().get("dark_mode", False)

# popup.py - Apply theme based on setting
self.dark_mode = credentials.is_dark_mode()
if self.dark_mode:
    bg_color = "#1F2937"
    text_color = "#F9FAFB"
else:
    bg_color = "#FFFFFF"
    text_color = "#1F2937"
```

### 8. Checkbox Not Clickable in Settings

**Problem**: Dark mode checkbox appeared but wasn't interactive.

**Solution**: Added explicit checkbox styling and increased dialog height:
```python
self.setFixedSize(500, 450)  # Was 400
self.setStyleSheet("""
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #D1D5DB;
        border-radius: 4px;
    }
    QCheckBox::indicator:checked {
        background-color: #3B82F6;
    }
""")
```

### 9. run.sh Repeatedly Asking for Dependencies

**Problem**: When running from conda environment, `run.sh` kept prompting to install system dependencies even though they were for GTK (which we no longer use).

**Solution**: Simplified `run.sh` to only handle venv creation and PySide6 installation:
```bash
setup_venv() {
    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
    fi
}
```

No system dependencies needed - PySide6 is pure Python wheels.

### 10. API Response Format

**Problem**: Initial implementation assumed different API response format.

**Solution**: Updated parsing to match actual Claude API response:
```python
# Actual format
data['five_hour']['utilization']  # Float 0.0-1.0
data['five_hour']['resets_at']    # ISO timestamp
data['seven_day']['utilization']
data['seven_day']['resets_at']
```

## Lessons Learned

1. **Qt > GTK for KDE** - When building for Plasma, use Qt
2. **Dynamic icons are possible** - QPainter can generate icons at runtime
3. **Test on target DE** - KDE Plasma behaves differently than GNOME
4. **Keep dependencies minimal** - PySide6 + requests is all we need
5. **Store config outside repo** - ~/.config/ keeps secrets safe
