"""Preflight checks for deployment/runtime readiness."""

from __future__ import annotations

import argparse
import json
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
    check_targets = [SETTINGS.history_file]
    if SETTINGS.heartbeat_file:
        check_targets.append(SETTINGS.heartbeat_file)

    for name in check_targets:
        p = Path(name)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8"):
                pass
            results.append((name, True, "writable"))
        except Exception as exc:
            results.append((name, False, f"not writable: {exc}"))
    return results




def check_data_integrity() -> List[Tuple[str, bool, str]]:
    checks = []
    for name in [SETTINGS.watchlist_file, SETTINGS.history_file]:
        p = Path(name)
        if not p.exists():
            checks.append((name, False, "missing (integrity check skipped)"))
            continue
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            checks.append((name, False, f"invalid json: {exc}"))
            continue

        if isinstance(payload, list):
            checks.append((name, True, "valid list json"))
        else:
            checks.append((name, False, "json root should be a list"))
    return checks

def check_env_hints() -> List[Tuple[str, bool, str]]:
    checks = []
    tg_ok = bool(os.getenv("TG_BOT_TOKEN")) and bool(os.getenv("TG_CHAT_ID"))
    checks.append(("telegram", tg_ok, "configured" if tg_ok else "not configured (console fallback)"))

    gate_key = bool(os.getenv("GATE_API_KEY"))
    gate_secret = bool(os.getenv("GATE_API_SECRET"))
    gate_ok = gate_key and gate_secret
    checks.append(("gate_api", gate_ok, "configured" if gate_ok else "not configured (watchlist fallback)"))
    return checks


def collect_preflight_report() -> dict:
    groups = {
        "required_files": check_required_files(),
        "writable_paths": check_writable_paths(),
        "data_integrity": check_data_integrity(),
        "environment_hints": check_env_hints(),
    }

    has_hard_fail = any(
        (not ok)
        for section in ("required_files", "writable_paths")
        for _key, ok, _msg in groups[section]
    )

    return {
        "status": "FAIL" if has_hard_fail else "PASS",
        "groups": {
            name: [
                {"key": key, "ok": ok, "message": message}
                for key, ok, message in rows
            ]
            for name, rows in groups.items()
        },
    }


def run_preflight(json_output: bool = False) -> int:
    report = collect_preflight_report()

    if json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["status"] == "FAIL" else 0

    title_map = {
        "required_files": "Required files",
        "writable_paths": "Writable paths",
        "data_integrity": "Data integrity",
        "environment_hints": "Environment hints",
    }

    hard_fail_sections = {"required_files", "writable_paths"}
    for section in ["required_files", "writable_paths", "data_integrity", "environment_hints"]:
        print(f"\n[{title_map[section]}]")
        for item in report["groups"][section]:
            if item["ok"]:
                mark = "OK"
            elif section in hard_fail_sections:
                mark = "FAIL"
            else:
                mark = "WARN"
            print(f"- {mark:4} {item['key']}: {item['message']}")

    print(f"\nPreflight result: {report['status']}")
    return 1 if report["status"] == "FAIL" else 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gate delist monitor preflight checker")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    raise SystemExit(run_preflight(json_output=args.json))
