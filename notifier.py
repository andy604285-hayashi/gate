"""Notification module (Phase 5, Telegram focused)."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import List

try:
    import requests
except ModuleNotFoundError:  # allow tests in constrained envs
    class _RequestsFallback:
        class RequestException(Exception):
            pass

        @staticmethod
        def post(*_args, **_kwargs):
            raise _RequestsFallback.RequestException("requests is not installed")

    requests = _RequestsFallback()  # type: ignore[assignment]

from config import SETTINGS
from scanner import Announcement

logger = logging.getLogger(__name__)

TELEGRAM_TEXT_LIMIT = 4096


def _fit_telegram_text(text: str, limit: int = TELEGRAM_TEXT_LIMIT) -> str:
    if len(text) <= limit:
        return text
    suffix = "\n\n...[truncated]"
    trimmed = text[: max(0, limit - len(suffix))]
    logger.warning("Telegram message exceeded %d chars; truncating", limit)
    return trimmed + suffix


def build_alert_message(
    ann: Announcement,
    delist_coins: List[str],
    danger_coins: List[str],
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_coins = sorted(set(delist_coins) - set(danger_coins))

    lines = [
        "🚨 Gate.io 下架警报 🚨",
        f"📅 时间：{now}",
        f"📢 公告：{ann.title}",
        f"🔗 链接：{ann.url}",
        f"📦 下架币种：{', '.join(delist_coins) if delist_coins else '未解析到'}",
    ]

    if danger_coins:
        lines.append("⚠️ 你持有的受影响币种：")
        lines.extend([f"  🔴 {coin} — 请立即处理" for coin in danger_coins])
    else:
        lines.append("✅ 当前持仓未命中本次下架币种")

    if safe_coins:
        lines.append(f"ℹ️ 其他下架币种：{', '.join(safe_coins)}")

    lines.append("⏰ 建议尽快登录交易所检查挂单并评估处理。")
    return "\n".join(lines)


def _telegram_send_once(text: str, timeout: int = 15) -> bool:
    if not SETTINGS.telegram_bot_token or not SETTINGS.telegram_chat_id:
        logger.info("Telegram not configured, skip remote send")
        return False

    url = f"https://api.telegram.org/bot{SETTINGS.telegram_bot_token}/sendMessage"
    payload = {"chat_id": SETTINGS.telegram_chat_id, "text": text}
    resp = requests.post(url, json=payload, timeout=timeout)
    return bool(getattr(resp, "ok", False))


def send_telegram_message(text: str, retries: int = 2, backoff_seconds: float = 1.5) -> bool:
    """Send Telegram message with simple retry/backoff.

    Returns True if any attempt succeeds, else False.
    """
    total_attempts = max(1, retries + 1)
    final_text = _fit_telegram_text(text)

    for attempt in range(1, total_attempts + 1):
        try:
            ok = _telegram_send_once(final_text)
            if ok:
                logger.info("Telegram send succeeded on attempt %d/%d", attempt, total_attempts)
                return True
            logger.warning("Telegram send returned non-OK on attempt %d/%d", attempt, total_attempts)
        except requests.RequestException as exc:
            logger.warning("Telegram send error on attempt %d/%d: %s", attempt, total_attempts, exc)

        if attempt < total_attempts:
            sleep_s = backoff_seconds * attempt
            time.sleep(sleep_s)

    logger.error("Telegram send failed after %d attempts", total_attempts)
    return False
