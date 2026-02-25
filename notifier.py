"""Notification module (Telegram focused)."""

from __future__ import annotations

from datetime import datetime
from typing import List

import requests

from config import SETTINGS
from scanner import Announcement


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
    ]

    if danger_coins:
        lines.append("⚠️ 你持有的受影响币种：")
        lines.extend([f"  🔴 {coin} — 请立即处理" for coin in danger_coins])
    else:
        lines.append("✅ 当前持仓未命中本次下架币种")

    if safe_coins:
        lines.append(f"ℹ️ 其他下架币种：{', '.join(safe_coins)}")

    return "\n".join(lines)


def send_telegram_message(text: str) -> bool:
    if not SETTINGS.telegram_bot_token or not SETTINGS.telegram_chat_id:
        return False

    url = f"https://api.telegram.org/bot{SETTINGS.telegram_bot_token}/sendMessage"
    payload = {"chat_id": SETTINGS.telegram_chat_id, "text": text}
    resp = requests.post(url, json=payload, timeout=15)
    return resp.ok
