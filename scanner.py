"""Announcement scanner module (Phase 2+)."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
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


def _pick_api_items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "list", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _parse_api_announcements(payload: object) -> List[Announcement]:
    rows = _pick_api_items(payload)
    out: List[Announcement] = []

    for row in rows:
        title = str(row.get("title") or row.get("name") or "").strip()
        if not title or not _is_delist_title(title):
            continue

        url = str(row.get("url") or row.get("link") or row.get("href") or "").strip()
        if url and url.startswith("/"):
            url = f"https://www.gate.io{url}"

        if not url:
            continue

        date_text = str(
            row.get("date")
            or row.get("time")
            or row.get("published_at")
            or row.get("created_at")
            or ""
        )
        out.append(Announcement(id=_extract_announcement_id(url, title), title=title, url=url, date=date_text))

    return _dedupe(out)


def _fetch_from_api() -> List[Announcement]:
    """Fetch announcements from optional API source if configured."""
    api_url = getattr(SETTINGS, "announcement_api_url", "")
    if not api_url:
        return []

    req = urllib.request.Request(api_url, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        payload = json.loads(resp.read().decode(charset, errors="replace"))
    return _parse_api_announcements(payload)


def _parse_rss_announcements(xml_text: str) -> List[Announcement]:
    root = ET.fromstring(xml_text)
    out: List[Announcement] = []

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        if not title or not _is_delist_title(title):
            continue

        url = (item.findtext("link") or "").strip()
        if not url:
            continue

        date_text = (item.findtext("pubDate") or "").strip()
        out.append(Announcement(id=_extract_announcement_id(url, title), title=title, url=url, date=date_text))

    return _dedupe(out)


def _fetch_from_rss() -> List[Announcement]:
    """Fetch announcements from optional RSS source if configured."""
    rss_url = getattr(SETTINGS, "announcement_rss_url", "")
    if not rss_url:
        return []

    req = urllib.request.Request(rss_url, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        xml_text = resp.read().decode(charset, errors="replace")
    return _parse_rss_announcements(xml_text)


def scan_announcements() -> List[Announcement]:
    """Aggregate announcements from all sources in priority order."""
    fetchers = [_fetch_from_api, _fetch_from_web, _fetch_from_rss]
    errors: list[str] = []
    merged: List[Announcement] = []

    for fetcher in fetchers:
        source_name = getattr(fetcher, "__name__", fetcher.__class__.__name__)
        try:
            items = fetcher()
            if items:
                logger.info("Scanner source=%s found %d delist announcements", source_name, len(items))
                merged.extend(items)
        except Exception as exc:
            errors.append(f"{source_name}: {exc}")
            logger.warning("Scanner source failed: %s", errors[-1])

    deduped = _dedupe(merged)
    if deduped:
        logger.info("Scanner merged %d announcements from %d sources", len(deduped), len(fetchers))
        return deduped

    if errors:
        logger.error("All scanner sources failed or yielded empty results: %s", " | ".join(errors))
    return []


def get_new_announcements() -> List[Announcement]:
    known_ids = _load_history(SETTINGS.history_file)
    current = scan_announcements()
    return [ann for ann in current if ann.id not in known_ids]
