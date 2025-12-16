"""Credential management for Claude Usage Monitor.

Supports multiple credential sources:
1. Manual session key input (like Usage4Claude)
2. Browser cookie extraction (Firefox, Chrome)
3. Claude Code OAuth tokens (fallback)
"""

import json
import os
import sqlite3
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

# Config file for manual credentials
CONFIG_DIR = Path.home() / ".config" / "claude-usage-monitor"
MANUAL_CREDS_FILE = CONFIG_DIR / "session.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# Claude Code credential file
CLAUDE_CODE_CREDS = Path.home() / ".claude" / ".credentials.json"


@dataclass
class ClaudeCredentials:
    """Claude authentication credentials."""
    session_key: str
    org_id: Optional[str] = None
    source: str = "unknown"  # "manual", "browser", "claude_code"
    subscription_type: str = "unknown"


def get_manual_credentials() -> Optional[Tuple[str, str]]:
    """Get manually saved session key and org ID."""
    if MANUAL_CREDS_FILE.exists():
        try:
            with open(MANUAL_CREDS_FILE, "r") as f:
                data = json.load(f)
                session_key = data.get("session_key")
                org_id = data.get("org_id")
                if session_key:
                    return session_key, org_id
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_manual_credentials(session_key: str, org_id: str) -> None:
    """Save manually entered credentials."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANUAL_CREDS_FILE, "w") as f:
        json.dump({"session_key": session_key, "org_id": org_id}, f)
    os.chmod(MANUAL_CREDS_FILE, 0o600)


def clear_manual_credentials() -> None:
    """Remove manually saved credentials."""
    if MANUAL_CREDS_FILE.exists():
        MANUAL_CREDS_FILE.unlink()


def get_browser_session_key() -> Optional[str]:
    """Try to extract session key from browser cookies."""
    # Try Firefox
    firefox_cookie = _get_firefox_cookie("claude.ai", "sessionKey")
    if firefox_cookie:
        return firefox_cookie

    # Try Chrome/Chromium
    chrome_cookie = _get_chrome_cookie("claude.ai", "sessionKey")
    if chrome_cookie:
        return chrome_cookie

    return None


def _get_firefox_cookie(domain: str, name: str) -> Optional[str]:
    """Extract a cookie from Firefox."""
    firefox_dir = Path.home() / ".mozilla" / "firefox"
    if not firefox_dir.exists():
        return None

    # Find profile directories
    for profile_dir in firefox_dir.iterdir():
        if not profile_dir.is_dir():
            continue
        cookie_db = profile_dir / "cookies.sqlite"
        if not cookie_db.exists():
            continue

        try:
            # Copy to temp file (Firefox locks the DB)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as tmp:
                shutil.copy2(cookie_db, tmp.name)
                tmp_path = tmp.name

            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM moz_cookies WHERE host LIKE ? AND name = ?",
                (f"%{domain}%", name)
            )
            result = cursor.fetchone()
            conn.close()
            os.unlink(tmp_path)

            if result:
                return result[0]
        except Exception:
            pass

    return None


def _get_chrome_cookie(domain: str, name: str) -> Optional[str]:
    """Extract a cookie from Chrome/Chromium (unencrypted only)."""
    # Chrome cookies are encrypted on Linux, this is a best-effort attempt
    chrome_paths = [
        Path.home() / ".config" / "google-chrome" / "Default" / "Cookies",
        Path.home() / ".config" / "chromium" / "Default" / "Cookies",
    ]

    for cookie_db in chrome_paths:
        if not cookie_db.exists():
            continue

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as tmp:
                shutil.copy2(cookie_db, tmp.name)
                tmp_path = tmp.name

            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM cookies WHERE host_key LIKE ? AND name = ?",
                (f"%{domain}%", name)
            )
            result = cursor.fetchone()
            conn.close()
            os.unlink(tmp_path)

            if result and result[0]:
                # Chrome encrypts cookies, so this might be empty
                return result[0]
        except Exception:
            pass

    return None


def get_claude_code_credentials() -> Optional[ClaudeCredentials]:
    """Read credentials from Claude Code's config."""
    if not CLAUDE_CODE_CREDS.exists():
        return None

    try:
        with open(CLAUDE_CODE_CREDS, "r") as f:
            data = json.load(f)

        oauth = data.get("claudeAiOauth", {})
        access_token = oauth.get("accessToken")
        if not access_token:
            return None

        return ClaudeCredentials(
            session_key=access_token,
            source="claude_code",
            subscription_type=oauth.get("subscriptionType", "unknown"),
        )
    except (json.JSONDecodeError, IOError, KeyError):
        return None


def get_credentials() -> Optional[ClaudeCredentials]:
    """Get credentials from best available source.

    Priority:
    1. Manual credentials (most reliable)
    2. Browser cookies
    3. Claude Code OAuth (may not work with web API)
    """
    # Try manual credentials first
    manual = get_manual_credentials()
    if manual:
        session_key, org_id = manual
        return ClaudeCredentials(
            session_key=session_key,
            org_id=org_id,
            source="manual",
        )

    # Try browser cookies
    browser_key = get_browser_session_key()
    if browser_key:
        return ClaudeCredentials(
            session_key=browser_key,
            source="browser",
        )

    # Fall back to Claude Code
    return get_claude_code_credentials()


def has_credentials() -> bool:
    """Check if any credentials are available."""
    return get_credentials() is not None


# App settings (dark mode, etc.)

def get_settings() -> dict:
    """Get app settings."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"dark_mode": False}


def save_settings(settings: dict) -> None:
    """Save app settings."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)


def is_dark_mode() -> bool:
    """Check if dark mode is enabled."""
    return get_settings().get("dark_mode", False)


def set_dark_mode(enabled: bool) -> None:
    """Set dark mode preference."""
    settings = get_settings()
    settings["dark_mode"] = enabled
    save_settings(settings)
