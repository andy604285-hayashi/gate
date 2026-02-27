"""Announcement scanner module (Phase 2)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from config import SETTINGS

logger = logging.getLogger(__name__)


@dataclass
class Announcement:
    id: str
    title: str
    url: str
    date: str


def _load_history(path: str) -> set[str]:
    file = Path(path)
    if not file.exists():
        return set()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        return set(data if isinstance(data, list) else [])
    except json.JSONDecodeError:
        return set()


def save_processed_ids(ids: Iterable[str], path: str | None = None) -> None:
    history_path = path or SETTINGS.history_file
    existing = _load_history(history_path)
    existing.update(ids)
    Path(history_path).write_text(
        json.dumps(sorted(existing), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _is_delist_title(title: str) -> bool:
    lowered = title.lower()
    return any(keyword.lower() in lowered for keyword in SETTINGS.delist_keywords)


def _extract_announcement_id(url: str, title: str) -> str:
    match = re.search(r"(\d{5,})", url)
    if match:
        return match.group(1)
    return re.sub(r"\W+", "-", title.lower()).strip("-")[:80]


def _dedupe(items: List[Announcement]) -> List[Announcement]:
    seen: set[str] = set()
    deduped: List[Announcement] = []
    for ann in items:
        if ann.id in seen:
            continue
        seen.add(ann.id)
        deduped.append(ann)
    return deduped


def _fetch_from_web() -> List[Announcement]:
    """Scrape Gate announcement page for delist-related announcements."""
    # Lazy imports so non-network/unit workflows can still import this module
    # in constrained environments where dependencies are unavailable.
    import requests
    from bs4 import BeautifulSoup

    resp = requests.get(SETTINGS.announcements_url, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items: List[Announcement] = []

    for link in soup.select("a[href]"):
        title = " ".join(link.get_text(strip=True).split())
        if not title or not _is_delist_title(title):
            continue

        href = link.get("href", "")
        if not href:
            continue

        if href.startswith("/"):
            url = f"https://www.gate.io{href}"
        elif href.startswith("http"):
            url = href
        else:
            continue

        item_id = _extract_announcement_id(url, title)
        date_text = ""
        parent_text = link.parent.get_text(" ", strip=True) if link.parent else ""
        date_match = re.search(r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})", parent_text)
        if date_match:
            date_text = date_match.group(1)

        items.append(Announcement(id=item_id, title=title, url=url, date=date_text))

    return _dedupe(items)


def _fetch_from_api() -> List[Announcement]:
    """Reserved for future API integration (phase roadmap)."""
    return []


def _fetch_from_rss() -> List[Announcement]:
    """Reserved for future RSS integration (phase roadmap)."""
    return []


def scan_announcements() -> List[Announcement]:
    """Try multiple sources in priority order and return latest scan result.

    Current phase strategy:
    1) API (placeholder)
    2) Web scraping (active)
    3) RSS (placeholder)
    """
    fetchers = [_fetch_from_api, _fetch_from_web, _fetch_from_rss]
    errors: list[str] = []

    for fetcher in fetchers:
        try:
            items = fetcher()
            if items:
                logger.info("Scanner source=%s found %d delist announcements", fetcher.__name__, len(items))
                return items
        except Exception as exc:  # keep scanner resilient; caller handles empty result
            errors.append(f"{fetcher.__name__}: {exc}")
            logger.warning("Scanner source failed: %s", errors[-1])

    if errors:
        logger.error("All scanner sources failed or yielded empty results: %s", " | ".join(errors))
    return []


def get_new_announcements() -> List[Announcement]:
    known_ids = _load_history(SETTINGS.history_file)
    current = scan_announcements()
    return [ann for ann in current if ann.id not in known_ids]
