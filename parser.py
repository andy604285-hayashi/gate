"""Announcement parser module (Phase 3)."""

from __future__ import annotations

import re
from typing import Iterable, List, Set

from scanner import Announcement

PAIR_RE = re.compile(r"\b([A-Z0-9]{2,15})\s*[/_]\s*(USDT|USD|BTC|ETH)\b")
TOKEN_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,14})\b")

STOPWORDS: Set[str] = {
    "GATE",
    "GATEIO",
    "ANNOUNCEMENT",
    "SPOT",
    "MARGIN",
    "FUTURES",
    "TRADING",
    "USDT",
    "USD",
    "BTC",
    "ETH",
    "THE",
    "AND",
    "WILL",
    "BE",
    "ON",
    "FOR",
    "WITH",
    "NOTICE",
    "SUSPENDED",
    "REMOVED",
    "DELIST",
    "REMOVE",
    "TOKEN",
    "TOKENS",
    "PAIR",
    "PAIRS",
}


def _normalize_tokens(candidates: Iterable[str]) -> List[str]:
    cleaned = {t.upper().strip() for t in candidates if t}
    return sorted(
        t
        for t in cleaned
        if t not in STOPWORDS
        and 2 <= len(t) <= 15
        and not t.isdigit()
    )


def extract_symbols_from_text(text: str) -> List[str]:
    """Extract candidate token symbols from free text.

    Strategy:
    1) collect base tokens from pair patterns like ABC/USDT or ABC_USDT
    2) collect uppercase token-like words
    3) normalize and drop stopwords/common non-symbol words
    """
    upper = text.upper()
    symbols = set(base for base, _quote in PAIR_RE.findall(upper))
    symbols.update(TOKEN_RE.findall(upper))
    return _normalize_tokens(symbols)


def _fetch_announcement_text(url: str) -> str:
    # Lazy imports to keep parser importable in restricted environments.
    import requests
    from bs4 import BeautifulSoup

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)


def parse_delist_coins(announcement: Announcement) -> List[str]:
    """Extract possible delisted token symbols from title + detail page text."""
    symbols = set(extract_symbols_from_text(announcement.title))
    detail_text = _fetch_announcement_text(announcement.url)
    symbols.update(extract_symbols_from_text(detail_text))
    return sorted(symbols)
