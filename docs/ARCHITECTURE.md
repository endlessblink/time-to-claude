# Architecture

## Overview

Claude Usage Monitor is a Linux system tray application built with PySide6 (Qt6 for Python). It displays Claude AI usage quotas with two tray icons and a popup window.

## Technology Stack

| Component | Technology | Why |
|-----------|------------|-----|
| GUI Framework | PySide6 (Qt6) | Native KDE Plasma 6 integration, LGPL license |
| HTTP Client | requests | Simple, reliable API calls |
| Icons | QPainter | Dynamic ring icons generated at runtime |
| Config Storage | JSON files | Simple, portable, no dependencies |

### Why PySide6 over GTK?

Initially the app was built with GTK/AppIndicator, but we switched to PySide6 because:

1. **KDE Plasma 6 is Qt-based** - Better native integration
2. **Dynamic icons** - QPainter makes it easy to draw ring progress indicators
3. **LGPL license** - More permissive than PyQt6's GPL
4. **Official Qt binding** - Maintained by the Qt Company

## Project Structure

```
claude-usage-monitor/
├── claude_usage_monitor/       # Main Python package
│   ├── __init__.py            # Package version
│   ├── main.py                # Entry point, QApplication setup
│   ├── tray.py                # QSystemTrayIcon, two icons (5h + 7d)
│   ├── popup.py               # Popup window with dual-ring widget
│   ├── settings.py            # Settings dialog (PySide6)
│   ├── api.py                 # Claude API client
│   ├── credentials.py         # Credential management
│   ├── config.py              # Legacy config (unused)
│   ├── icons.py               # Legacy icons (unused)
│   ├── indicator.py           # Legacy GTK indicator (unused)
│   └── ui/                    # Legacy UI modules (unused)
├── docs/                      # Documentation
├── icons/                     # SVG icons (unused, using QPainter now)
├── requirements.txt           # Python dependencies
├── run.sh                     # Portable launcher script
└── .venv/                     # Virtual environment (auto-created)
```

## Key Components

### 1. Tray Icons (`tray.py`)

Two `QSystemTrayIcon` instances:
- **Primary icon**: 5-hour usage (green → orange → red)
- **Secondary icon**: 7-day usage (cyan → purple → deep purple)

Icons are generated dynamically using `create_ring_icon()`:
```python
def create_ring_icon(percentage: int, color: QColor, size: int = 22) -> QIcon:
    # Creates a circular progress ring with percentage number inside
    pixmap = QPixmap(size, size)
    painter = QPainter(pixmap)
    # Draw background track, progress arc, centered number
    painter.drawArc(rect, start_angle, span_angle)
```

### 2. Popup Window (`popup.py`)

A frameless `QWidget` with:
- **DualRingWidget**: Custom widget drawing two concentric progress rings
- **TimerRow**: Shows period (5h/7d), time remaining, reset time
- **Dark mode support**: Reads setting from credentials module

Window flags:
```python
Qt.WindowType.Tool |           # Doesn't steal focus
Qt.WindowType.FramelessWindowHint |
Qt.WindowType.WindowStaysOnTopHint
```

### 3. API Client (`api.py`)

Fetches usage data from Claude's internal API:
```
GET https://claude.ai/api/organizations/{org_id}/usage
Cookie: sessionKey={session_key}
```

Response parsing:
```python
data['five_hour']['utilization']  # 0.0 to 1.0
data['seven_day']['utilization']  # 0.0 to 1.0
data['five_hour']['resets_at']    # ISO timestamp
```

### 4. Credentials (`credentials.py`)

Stores credentials in `~/.config/claude-usage-monitor/`:
- `session.json` - Session key and org ID
- `settings.json` - Dark mode preference

Supports multiple credential sources (priority order):
1. Manual entry (Settings dialog)
2. Browser cookie extraction (Firefox/Chrome)
3. Claude Code OAuth tokens

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Claude.ai  │────▶│   api.py    │────▶│  tray.py    │
│    API      │     │ fetch_usage │     │ update icons│
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  UsageData  │────▶│  popup.py   │
                    │  dataclass  │     │ update rings│
                    └─────────────┘     └─────────────┘
```

## Refresh Cycle

1. **Initial refresh**: 500ms after startup
2. **Periodic refresh**: Every 5 minutes (`QTimer`)
3. **Manual refresh**: Click refresh button in popup

## Configuration Storage

All config stored in `~/.config/claude-usage-monitor/`:

```json
// session.json
{
  "session_key": "sk-ant-sid01-...",
  "org_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}

// settings.json
{
  "dark_mode": true
}
```
