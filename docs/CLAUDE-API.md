# Claude API Integration

## How Claude Usage Limits Work

Claude Pro and Team subscriptions have two usage limits:

### 5-Hour Limit (Short-term)
- Resets every 5 hours from when you started using it
- Prevents burst usage
- Shows as the **outer ring** (green/orange/red)

### 7-Day Limit (Long-term)
- Rolling 7-day window
- Overall usage cap
- Shows as the **inner ring** (cyan/purple)

## API Endpoint

The app uses Claude's internal usage API (same as the web interface):

```
GET https://claude.ai/api/organizations/{org_id}/usage
```

### Authentication

Requires browser session cookie:
```
Cookie: sessionKey=sk-ant-sid01-...
```

The session key can be found in browser dev tools:
1. Open claude.ai
2. F12 → Application → Cookies → claude.ai
3. Copy `sessionKey` value

### Response Format

```json
{
  "five_hour": {
    "utilization": 0.19,
    "resets_at": "2025-12-16T18:00:00Z"
  },
  "seven_day": {
    "utilization": 0.12,
    "resets_at": "2025-12-23T08:00:00Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `utilization` | float | Usage as decimal (0.0 to 1.0) |
| `resets_at` | string | ISO 8601 timestamp of next reset |

## Organization ID

The org ID is needed for the API call. It can be found in:
- The URL when on claude.ai: `claude.ai/chat/{org_id}`
- Network requests in browser dev tools

If not provided, the app attempts to fetch it from:
```
GET https://claude.ai/api/organizations
```

## API Client Implementation

Located in `claude_usage_monitor/api.py`:

```python
class ClaudeAPI:
    BASE_URL = "https://claude.ai/api"

    def __init__(self):
        creds = credentials.get_credentials()
        self.session_key = creds.session_key
        self.org_id = creds.org_id or self._fetch_org_id()

    def fetch_usage(self) -> UsageData:
        url = f"{self.BASE_URL}/organizations/{self.org_id}/usage"
        headers = {"Cookie": f"sessionKey={self.session_key}"}
        response = requests.get(url, headers=headers)
        return self._parse_response(response.json())
```

## UsageData Dataclass

```python
@dataclass
class UsageData:
    is_connected: bool
    short_term_usage: float      # 0.0 to 1.0
    long_term_usage: float       # 0.0 to 1.0
    short_term_reset: datetime   # Next 5h reset
    long_term_reset: datetime    # Next 7d reset
    short_term_reset_str: str    # "3h 45m"
    long_term_reset_str: str     # "6d 2h"

    @property
    def short_term_percent(self) -> int:
        return int(self.short_term_usage * 100)

    @property
    def long_term_percent(self) -> int:
        return int(self.long_term_usage * 100)
```

## Color Thresholds

### 5-Hour Usage Colors
| Usage | Color | Hex |
|-------|-------|-----|
| < 70% | Green | #22C55E |
| 70-90% | Orange | #F97316 |
| > 90% | Red | #EF4444 |

### 7-Day Usage Colors
| Usage | Color | Hex |
|-------|-------|-----|
| < 70% | Cyan | #06B6D4 |
| 70-90% | Purple | #8B5CF6 |
| > 90% | Deep Purple | #7C3AED |

## Error Handling

The API client handles:
- **Network errors**: Returns disconnected state
- **Auth errors (401/403)**: Session key expired
- **Missing org ID**: Attempts to fetch from /organizations endpoint

```python
def fetch_usage(self) -> UsageData:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return self._parse_response(response.json())
    except requests.RequestException:
        pass
    return UsageData(is_connected=False, ...)
```

## Refresh Schedule

- **On startup**: 500ms delay
- **Periodic**: Every 5 minutes
- **Manual**: Refresh button in popup

```python
self.refresh_timer = QTimer()
self.refresh_timer.timeout.connect(self.refresh)
self.refresh_timer.start(5 * 60 * 1000)  # 5 minutes
```
