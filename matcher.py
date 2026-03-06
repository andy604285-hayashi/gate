"""Portfolio/watchlist matching module (Phase 4)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from pathlib import Path
from typing import List

try:
    import requests
except ModuleNotFoundError:  # allow offline/unit environments without deps
    class _RequestsFallback:
        class RequestException(Exception):
            pass

        @staticmethod
        def get(*_args, **_kwargs):
            raise _RequestsFallback.RequestException("requests is not installed")

    requests = _RequestsFallback()  # type: ignore[assignment]

from config import SETTINGS

logger = logging.getLogger(__name__)


class GateAuthConfigError(ValueError):
    """Raised when Gate credentials are incomplete."""


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
    key = SETTINGS.gate_api_key
    secret = SETTINGS.gate_api_secret

    if not key and not secret:
        logger.info("Gate API credentials not configured; skip API balance fetch")
        return []
    if not key or not secret:
        raise GateAuthConfigError("Both GATE_API_KEY and GATE_API_SECRET must be set together")

    path = "/spot/accounts"
    url = f"{SETTINGS.gate_api_base}{path}"
    headers = _gate_headers("GET", path)

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    tokens = []
    for row in data:
        currency = row.get("currency", "").upper()
        try:
            available = float(row.get("available", 0) or 0)
            locked = float(row.get("locked", 0) or 0)
        except (TypeError, ValueError):
            logger.debug("Skip malformed balance row: %s", row)
            continue
        if currency and (available > 0 or locked > 0):
            tokens.append(currency)

    normalized = sorted(set(tokens))
    logger.info("Fetched %d symbols from Gate spot balances", len(normalized))
    return normalized


def _load_watchlist() -> List[str]:
    file = Path(SETTINGS.watchlist_file)
    if not file.exists():
        logger.info("Watchlist file not found: %s", SETTINGS.watchlist_file)
        return []

    try:
        content = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Watchlist JSON is invalid: %s", SETTINGS.watchlist_file)
        return []

    if isinstance(content, list):
        normalized: set[str] = set()
        for item in content:
            if item is None:
                continue
            token = str(item).strip().upper()
            if token:
                normalized.add(token)

        tokens = sorted(normalized)
        logger.info("Loaded %d symbols from watchlist", len(tokens))
        return tokens

    logger.warning("Watchlist JSON must be a list: %s", SETTINGS.watchlist_file)
    return []


def get_my_coins() -> List[str]:
    watchlist_tokens = _load_watchlist()

    try:
        api_tokens = _fetch_spot_balances()
    except GateAuthConfigError as exc:
        logger.warning("Gate credential configuration issue, fallback to watchlist only: %s", exc)
        api_tokens = []
    except requests.RequestException as exc:
        logger.warning("Failed to fetch Gate spot balances, fallback to watchlist only: %s", exc)
        api_tokens = []

    merged = sorted(set(api_tokens) | set(watchlist_tokens))
    logger.info(
        "Portfolio source summary: api=%d watchlist=%d merged=%d",
        len(api_tokens),
        len(watchlist_tokens),
        len(merged),
    )
    return merged


def _normalize_symbols(values: List[str]) -> set[str]:
    out: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip().upper()
        if text:
            out.add(text)
    return out


def match_coins(delist_coins: List[str], my_coins: List[str]) -> List[str]:
    return sorted(_normalize_symbols(delist_coins) & _normalize_symbols(my_coins))
