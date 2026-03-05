"""Preflight checks for deployment/runtime readiness."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import SETTINGS


def check_required_files() -> List[Tuple[str, bool, str]]:
    checks = []
    for name in [SETTINGS.watchlist_file, SETTINGS.history_file]:
        p = Path(name)
        ok = p.exists()
        msg = "exists" if ok else "missing"
        checks.append((name, ok, msg))
    return checks


def check_writable_paths() -> List[Tuple[str, bool, str]]:
    results = []
    for name in [SETTINGS.history_file]:
        p = Path(name)
        try:
            if p.exists():
                with p.open("a", encoding="utf-8"):
                    pass
            else:
                p.write_text("[]", encoding="utf-8")
            results.append((name, True, "writable"))
        except Exception as exc:
            results.append((name, False, f"not writable: {exc}"))
    return results


def check_env_hints() -> List[Tuple[str, bool, str]]:
    checks = []
    tg_ok = bool(os.getenv("TG_BOT_TOKEN")) and bool(os.getenv("TG_CHAT_ID"))
    checks.append(("telegram", tg_ok, "configured" if tg_ok else "not configured (console fallback)"))

    gate_key = bool(os.getenv("GATE_API_KEY"))
    gate_secret = bool(os.getenv("GATE_API_SECRET"))
    gate_ok = gate_key and gate_secret
    checks.append(("gate_api", gate_ok, "configured" if gate_ok else "not configured (watchlist fallback)"))
    return checks


def run_preflight() -> int:
    groups = [
        ("Required files", check_required_files()),
        ("Writable paths", check_writable_paths()),
        ("Environment hints", check_env_hints()),
    ]

    has_hard_fail = False
    for title, rows in groups:
        print(f"\n[{title}]")
        for key, ok, msg in rows:
            mark = "OK" if ok else "WARN"
            print(f"- {mark:4} {key}: {msg}")
            if title in {"Required files", "Writable paths"} and not ok:
                has_hard_fail = True

    if has_hard_fail:
        print("\nPreflight result: FAIL")
        return 1
    print("\nPreflight result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_preflight())
