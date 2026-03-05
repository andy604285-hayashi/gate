"""Main entry point for Gate.io delist monitor (Phase 6+)."""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from config import SETTINGS
from matcher import get_my_coins, match_coins
from notifier import build_alert_message, send_telegram_message
from parser import parse_delist_coins
from scanner import get_new_announcements, save_processed_ids

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _status_payload() -> dict:
    return {
        "poll_interval_seconds": SETTINGS.poll_interval_seconds,
        "history_file": SETTINGS.history_file,
        "watchlist_file": SETTINGS.watchlist_file,
        "announcement_web": SETTINGS.announcements_url,
        "announcement_api_configured": bool(SETTINGS.announcement_api_url),
        "announcement_rss_configured": bool(SETTINGS.announcement_rss_url),
        "gate_api_configured": bool(SETTINGS.gate_api_key and SETTINGS.gate_api_secret),
        "telegram_configured": bool(SETTINGS.telegram_bot_token and SETTINGS.telegram_chat_id),
        "heartbeat_configured": bool(SETTINGS.heartbeat_file),
    }


def print_status(json_output: bool = False) -> None:
    """Print non-secret runtime status for quick diagnostics."""
    payload = _status_payload()
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    logger.info("Runtime status summary:")
    for key, value in payload.items():
        logger.info("- %s=%s", key, value)




def write_heartbeat(status: str, processed: int = 0, error: str = "") -> None:
    """Write optional heartbeat JSON for external liveness checks."""
    if not SETTINGS.heartbeat_file:
        return

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "processed": processed,
        "error": error,
    }
    Path(SETTINGS.heartbeat_file).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def run_once(dry_run: bool = False) -> int:
    """Run one polling cycle.

    Returns the number of newly processed announcements.
    """
    announcements = get_new_announcements()
    if not announcements:
        logger.info("No new delist announcements")
        write_heartbeat(status="idle", processed=0)
        return 0

    my_coins = get_my_coins()
    processed_count = 0

    for ann in announcements:
        try:
            delist_coins = parse_delist_coins(ann)
            danger_coins = match_coins(delist_coins, my_coins)
            message = build_alert_message(ann, delist_coins, danger_coins)

            if dry_run:
                logger.info("DRY RUN: alert generated but not sent/saved: %s", ann.title)
                logger.debug("DRY RUN alert message:\n%s", message)
                processed_count += 1
                continue

            if send_telegram_message(message):
                logger.info("ALERT SENT: %s", ann.title)
            else:
                logger.info("ALERT GENERATED (telegram skipped/failed): %s", ann.title)
                logger.debug("Generated alert message:\n%s", message)

            # Persist each successfully handled announcement immediately.
            save_processed_ids([ann.id])
            processed_count += 1
        except Exception as exc:  # keep batch resilient per-announcement
            logger.exception("ANNOUNCEMENT ERROR: %s (%s)", ann.title, exc)

    logger.info(
        "Cycle complete: processed=%d total_candidates=%d dry_run=%s",
        processed_count,
        len(announcements),
        dry_run,
    )
    write_heartbeat(status="ok", processed=processed_count)
    return processed_count


def run_loop(max_cycles: int | None = None, dry_run: bool = False) -> None:
    logger.info("Gate.io 下架监控已启动 (interval=%ss dry_run=%s)", SETTINGS.poll_interval_seconds, dry_run)
    cycles = 0
    while True:
        try:
            run_once(dry_run=dry_run)
        except Exception as exc:  # broad guard for long-running monitor
            logger.exception("TOP-LEVEL LOOP ERROR: %s", exc)
            write_heartbeat(status="error", processed=0, error=str(exc))

        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            logger.info("Reached max cycles (%d), loop exits", max_cycles)
            return

        time.sleep(SETTINGS.poll_interval_seconds)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gate.io delist monitor")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one cycle only and exit (useful for cron/testing)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level: DEBUG/INFO/WARNING/ERROR",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run deployment preflight checks and exit",
    )
    parser.add_argument(
        "--preflight-json",
        action="store_true",
        help="When used with --preflight, emit JSON output",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print runtime status summary and exit",
    )
    parser.add_argument(
        "--status-json",
        action="store_true",
        help="When used with --status, emit JSON output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without sending notifications or writing history",
    )
    parser.add_argument(
        "--once-json",
        action="store_true",
        help="When used with --once, emit JSON summary",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    setup_logging(args.log_level)

    for warning in SETTINGS.validation_warnings():
        logger.warning("CONFIG WARNING: %s", warning)

    if args.preflight:
        from tools.preflight_check import run_preflight

        raise SystemExit(run_preflight(json_output=args.preflight_json))

    if args.status:
        print_status(json_output=args.status_json)
        return

    if args.once:
        processed = run_once(dry_run=args.dry_run)
        if args.once_json:
            print(json.dumps({"processed": processed, "dry_run": bool(args.dry_run)}, ensure_ascii=False))
        return

    run_loop(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
