"""Configuration for Gate.io delist monitor.

Copy this file and fill credentials before production use.
"""

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
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))

    telegram_bot_token: str = os.getenv("TG_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TG_CHAT_ID", "")

    # Keyword matching for announcement title pre-filtering.
    delist_keywords: List[str] = None  # type: ignore[assignment]

    history_file: str = os.getenv("HISTORY_FILE", "history.json")
    watchlist_file: str = os.getenv("WATCHLIST_FILE", "watchlist.json")

    def __post_init__(self) -> None:
        if self.delist_keywords is None:
            object.__setattr__(
                self,
                "delist_keywords",
                ["delist", "remove", "下架", "移除"],
            )


SETTINGS = Settings()
