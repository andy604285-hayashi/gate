"""Phase-1 data-source probe utility.

This script intentionally uses stdlib only, so it can run even when
third-party dependencies are unavailable in restricted environments.
"""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request

CANDIDATES = [
    "https://www.gate.io/announcements",
    "https://api.gateio.ws/api/v4",
    "https://www.gate.io/announcements/rss",
    "https://www.gate.io/rss",
]


def probe(url: str) -> str:
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as resp:
            return f"OK {resp.status} {resp.getheader('Content-Type', '')}"
    except urllib.error.HTTPError as exc:
        return f"HTTPError {exc.code}"
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return f"Error {type(exc).__name__}: {exc}"


def main() -> None:
    print("Gate.io source probe")
    for url in CANDIDATES:
        print(f"- {url}: {probe(url)}")


if __name__ == "__main__":
    main()
