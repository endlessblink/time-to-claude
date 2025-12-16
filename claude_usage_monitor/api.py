"""Claude API integration for fetching usage data."""

import requests
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from . import credentials


@dataclass
class UsageData:
    """Container for Claude usage information."""
    # 5-hour (short-term) quota
    short_term_usage: float = 0.0  # 0.0 to 1.0
    short_term_reset: Optional[datetime] = None

    # Daily/weekly (long-term) quota
    long_term_usage: float = 0.0  # 0.0 to 1.0
    long_term_reset: Optional[datetime] = None

    # Account info
    subscription_type: str = "unknown"
    credential_source: str = "unknown"

    # Status
    is_connected: bool = False
    error: Optional[str] = None

    @property
    def short_term_percent(self) -> int:
        return int(self.short_term_usage * 100)

    @property
    def long_term_percent(self) -> int:
        return int(self.long_term_usage * 100)

    @property
    def max_usage(self) -> float:
        return max(self.short_term_usage, self.long_term_usage)

    def _format_reset(self, reset_time: Optional[datetime]) -> str:
        if not reset_time:
            return "Unknown"
        now = datetime.now(timezone.utc)
        if reset_time.tzinfo is None:
            reset_time = reset_time.replace(tzinfo=timezone.utc)
        delta = reset_time - now
        total_seconds = delta.total_seconds()
        if total_seconds <= 0:
            return "Now"
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @property
    def short_term_reset_str(self) -> str:
        return self._format_reset(self.short_term_reset)

    @property
    def long_term_reset_str(self) -> str:
        return self._format_reset(self.long_term_reset)


class ClaudeAPI:
    """Client for fetching Claude usage data."""

    BASE_URL = "https://claude.ai/api/organizations"

    def __init__(self):
        self.session = requests.Session()
        self.creds = credentials.get_credentials()
        self._setup_session()

    def _setup_session(self) -> None:
        """Configure session with browser-like headers."""
        if not self.creds:
            return

        # Headers that mimic Chrome browser
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "anthropic-client-platform": "web_claude_ai",
            "anthropic-client-version": "1.0.0",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "origin": "https://claude.ai",
            "referer": "https://claude.ai/settings/usage",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
        })

        # Set session cookie
        self.session.cookies.set("sessionKey", self.creds.session_key, domain="claude.ai")

    def fetch_usage(self) -> UsageData:
        """Fetch current usage data from Claude API."""
        if not self.creds:
            return UsageData(error="No credentials. Click Settings to configure.")

        # Get org ID (from creds or API)
        org_id = self.creds.org_id or self._get_organization_id()
        if not org_id:
            return UsageData(
                subscription_type=self.creds.subscription_type,
                credential_source=self.creds.source,
                error="Could not get organization ID. Check your session key.",
            )

        try:
            url = f"{self.BASE_URL}/{org_id}/usage"
            response = self.session.get(url, timeout=15)

            if response.status_code == 200:
                usage = self._parse_usage_response(response.json())
                usage.credential_source = self.creds.source
                return usage
            elif response.status_code == 401:
                return UsageData(
                    credential_source=self.creds.source,
                    error="Session expired. Update your session key.",
                )
            elif response.status_code == 403:
                if "Just a moment" in response.text:
                    return UsageData(
                        credential_source=self.creds.source,
                        error="Blocked by Cloudflare. Try again later.",
                    )
                return UsageData(
                    credential_source=self.creds.source,
                    error="Access forbidden",
                )
            else:
                return UsageData(
                    credential_source=self.creds.source,
                    error=f"HTTP {response.status_code}",
                )

        except requests.exceptions.Timeout:
            return UsageData(credential_source=self.creds.source, error="Timed out")
        except requests.exceptions.ConnectionError:
            return UsageData(credential_source=self.creds.source, error="Connection failed")
        except Exception as e:
            return UsageData(credential_source=self.creds.source, error=str(e))

    def _get_organization_id(self) -> Optional[str]:
        """Try to get the organization ID from the API."""
        try:
            response = self.session.get("https://claude.ai/api/bootstrap", timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Try various response structures
                if "account" in data:
                    account = data["account"]
                    if "memberships" in account and account["memberships"]:
                        return account["memberships"][0].get("organization", {}).get("uuid")
                if "organizations" in data and data["organizations"]:
                    org = data["organizations"][0]
                    return org.get("uuid") or org.get("id")
        except Exception:
            pass
        return None

    def _parse_usage_response(self, data: dict) -> UsageData:
        """Parse the usage API response."""
        usage = UsageData(
            subscription_type=self.creds.subscription_type if self.creds else "unknown",
            is_connected=True,
        )

        try:
            # Parse short-term (5-hour) quota - new format
            if "five_hour" in data:
                five_hour = data["five_hour"]
                if isinstance(five_hour, dict):
                    usage.short_term_usage = five_hour.get("utilization", 0) / 100
                    if "resets_at" in five_hour:
                        usage.short_term_reset = self._parse_timestamp(five_hour["resets_at"])
            # Legacy format fallback
            elif "dailyUsage" in data:
                daily = data["dailyUsage"]
                if isinstance(daily, dict):
                    usage.short_term_usage = daily.get("percentUsed", 0) / 100
                    if "resetsAt" in daily:
                        usage.short_term_reset = self._parse_timestamp(daily["resetsAt"])

            # Parse long-term (7-day) quota - new format
            if "seven_day" in data:
                seven_day = data["seven_day"]
                if isinstance(seven_day, dict):
                    usage.long_term_usage = seven_day.get("utilization", 0) / 100
                    if "resets_at" in seven_day:
                        usage.long_term_reset = self._parse_timestamp(seven_day["resets_at"])
            # Legacy format fallback
            elif "longTermUsage" in data:
                long_term = data["longTermUsage"]
                if isinstance(long_term, dict):
                    usage.long_term_usage = long_term.get("percentUsed", 0) / 100
                    if "resetsAt" in long_term:
                        usage.long_term_reset = self._parse_timestamp(long_term["resetsAt"])

        except (KeyError, TypeError, ValueError):
            pass

        return usage

    def _parse_timestamp(self, ts) -> Optional[datetime]:
        """Parse various timestamp formats."""
        if not ts:
            return None
        try:
            if isinstance(ts, (int, float)):
                if ts > 1e12:
                    ts = ts / 1000
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            if isinstance(ts, str):
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, OSError):
            pass
        return None
