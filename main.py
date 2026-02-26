"""Main entry point for Gate.io delist monitor."""

from __future__ import annotations

import time

from config import SETTINGS
from matcher import get_my_coins, match_coins
from notifier import build_alert_message, send_telegram_message
from parser import parse_delist_coins
from scanner import get_new_announcements, save_processed_ids


def run_once() -> None:
    announcements = get_new_announcements()
    if not announcements:
        print("No new delist announcements.")
        return

    my_coins = get_my_coins()

    for ann in announcements:
        try:
            delist_coins = parse_delist_coins(ann)
            danger_coins = match_coins(delist_coins, my_coins)
            message = build_alert_message(ann, delist_coins, danger_coins)

            if send_telegram_message(message):
                print(f"[ALERT SENT] {ann.title}")
            else:
                print(f"[ALERT GENERATED] {ann.title}\n{message}")

            # Persist each successfully handled announcement immediately,
            # so a later failure in the same polling batch won't cause
            # duplicate alerts for already-processed items.
            save_processed_ids([ann.id])
        except Exception as exc:
            print(f"[ANNOUNCEMENT ERROR] {ann.title}: {exc}")


def main() -> None:
    print("🚀 Gate.io 下架监控已启动")
    while True:
        try:
            run_once()
        except Exception as exc:  # broad guard for long-running monitor
            print(f"[ERROR] {exc}")
        time.sleep(SETTINGS.poll_interval_seconds)


if __name__ == "__main__":
    main()
