"""Announcement parser module."""

from __future__ import annotations

import re
from typing import Iterable, List, Set

import requests
from bs4 import BeautifulSoup

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
}


def _normalize_tokens(candidates: Iterable[str]) -> List[str]:
    cleaned = {t.upper().strip() for t in candidates if t}
    return sorted(t for t in cleaned if t not in STOPWORDS)


def parse_delist_coins(announcement: Announcement) -> List[str]:
    """Extract possible delisted token symbols from title + detail page text."""
    symbols = set(TOKEN_RE.findall(announcement.title.upper()))
    symbols.update(base for base, _quote in PAIR_RE.findall(announcement.title.upper()))

    resp = requests.get(announcement.url, timeout=15)
    resp.raise_for_status()
    text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)

    symbols.update(TOKEN_RE.findall(text.upper()))
    symbols.update(base for base, _quote in PAIR_RE.findall(text.upper()))

    return _normalize_tokens(symbols)
