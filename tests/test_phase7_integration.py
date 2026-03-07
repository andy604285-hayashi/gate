import unittest
from unittest.mock import patch

import main
from scanner import Announcement


class Phase7IntegrationTests(unittest.TestCase):
    def test_pipeline_integration_single_announcement(self) -> None:
        ann = Announcement(id="42", title="Delist ABC", url="https://example/a", date="2026-01-01")

        with patch("main.get_new_announcements", return_value=[ann]), \
            patch("main.get_my_coins", return_value=["ABC", "ETH"]), \
            patch("main.parse_delist_coins", return_value=["ABC", "XYZ"]), \
            patch("main.match_coins", return_value=["ABC"]), \
            patch("main.build_alert_message", return_value="msg") as build_mock, \
            patch("main.send_telegram_message", return_value=True) as send_mock, \
            patch("main.save_processed_ids") as save_mock:
            out = main.run_once()

        self.assertEqual(out, 1)
        build_mock.assert_called_once()
        send_mock.assert_called_once_with("msg")
        save_mock.assert_called_once_with(["42"])

    def test_run_loop_with_max_cycles(self) -> None:
        with patch("main.run_once", return_value=0) as run_once_mock, \
            patch("main.time.sleep") as sleep_mock:
            main.run_loop(max_cycles=3)

        self.assertEqual(run_once_mock.call_count, 3)
        self.assertEqual(sleep_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
