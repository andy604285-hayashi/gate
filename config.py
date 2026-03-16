"""Configuration for Gate.io delist monitor."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Settings:
    gate_api_key: str = os.getenv("GATE_API_KEY", "")
    gate_api_secret: str = os.getenv("GATE_API_SECRET", "")
    gate_api_base: str = os.getenv("GATE_API_BASE", "https://api.gateio.ws/api/v4")
    announcements_url: str = os.getenv("GATE_ANNOUNCEMENTS_URL", "https://www.gate.io/announcements")
    announcement_api_url: str = os.getenv("GATE_ANNOUNCEMENT_API_URL", "")
    announcement_rss_url: str = os.getenv("GATE_ANNOUNCEMENT_RSS_URL", "")
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))

    telegram_bot_token: str = os.getenv("TG_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TG_CHAT_ID", "")

    delist_keywords: List[str] = None  # type: ignore[assignment]

    history_file: str = os.getenv("HISTORY_FILE", "history.json")
    watchlist_file: str = os.getenv("WATCHLIST_FILE", "watchlist.json")
    heartbeat_file: str = os.getenv("HEARTBEAT_FILE", "")

    def __post_init__(self) -> None:
        if self.delist_keywords is None:
            object.__setattr__(self, "delist_keywords", ["delist", "remove", "下架", "移除"])

    def validation_warnings(self) -> List[str]:
        """Non-fatal configuration warnings for startup diagnostics."""
        warnings: List[str] = []

        if self.poll_interval_seconds <= 0:
            warnings.append("POLL_INTERVAL_SECONDS should be > 0.")

        # Pairs of secrets should be configured together.
        if bool(self.gate_api_key) ^ bool(self.gate_api_secret):
            warnings.append("GATE_API_KEY and GATE_API_SECRET should be set together.")

        if bool(self.telegram_bot_token) ^ bool(self.telegram_chat_id):
            warnings.append("TG_BOT_TOKEN and TG_CHAT_ID should be set together.")

        if not self.telegram_bot_token or not self.telegram_chat_id:
            warnings.append("Telegram not fully configured; alerts will fall back to console logging.")

        return warnings


SETTINGS = Settings()
