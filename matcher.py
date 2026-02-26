"""Portfolio/watchlist matching module."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from pathlib import Path
from typing import List

import requests

from config import SETTINGS


logger = logging.getLogger(__name__)


def _gate_headers(method: str, path: str, query_string: str = "", body: str = "") -> dict[str, str]:
    t = str(int(time.time()))
    payload_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
    sign_str = "\n".join([method, path, query_string, payload_hash, t])
    signature = hmac.new(
        SETTINGS.gate_api_secret.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
    return {"KEY": SETTINGS.gate_api_key, "Timestamp": t, "SIGN": signature}


def _fetch_spot_balances() -> List[str]:
    if not SETTINGS.gate_api_key or not SETTINGS.gate_api_secret:
        return []

    path = "/spot/accounts"
    url = f"{SETTINGS.gate_api_base}{path}"
    headers = _gate_headers("GET", path)

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    tokens = []
    for row in data:
        currency = row.get("currency", "").upper()
        available = float(row.get("available", 0) or 0)
        locked = float(row.get("locked", 0) or 0)
        if currency and (available > 0 or locked > 0):
            tokens.append(currency)
    return sorted(set(tokens))


def _load_watchlist() -> List[str]:
    file = Path(SETTINGS.watchlist_file)
    if not file.exists():
        return []

    try:
        content = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if isinstance(content, list):
        return sorted({str(c).upper() for c in content})
    return []


def get_my_coins() -> List[str]:
    watchlist_tokens = _load_watchlist()

    try:
        api_tokens = _fetch_spot_balances()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch Gate spot balances, fallback to watchlist only: %s", exc)
        api_tokens = []

    return sorted(set(api_tokens) | set(watchlist_tokens))


def match_coins(delist_coins: List[str], my_coins: List[str]) -> List[str]:
    return sorted(set(c.upper() for c in delist_coins) & set(c.upper() for c in my_coins))
