import unittest
from unittest.mock import patch

import main
from scanner import Announcement


class MainCoreTests(unittest.TestCase):
    def test_run_once_no_announcements(self) -> None:
        with patch("main.get_new_announcements", return_value=[]):
            out = main.run_once()
        self.assertEqual(out, 0)

    def test_run_once_processes_and_saves_each_id(self) -> None:
        anns = [
            Announcement(id="1", title="t1", url="u1", date=""),
            Announcement(id="2", title="t2", url="u2", date=""),
        ]
        with patch("main.get_new_announcements", return_value=anns), \
            patch("main.get_my_coins", return_value=["ABC"]), \
            patch("main.parse_delist_coins", return_value=["ABC"]), \
            patch("main.match_coins", return_value=["ABC"]), \
            patch("main.build_alert_message", return_value="msg"), \
            patch("main.send_telegram_message", return_value=True), \
            patch("main.save_processed_ids") as save_mock:
            out = main.run_once()

        self.assertEqual(out, 2)
        self.assertEqual(save_mock.call_count, 2)

    def test_run_once_continues_when_one_announcement_fails(self) -> None:
        anns = [
            Announcement(id="1", title="bad", url="u1", date=""),
            Announcement(id="2", title="good", url="u2", date=""),
        ]

        def parse_side_effect(ann: Announcement):
            if ann.id == "1":
                raise RuntimeError("boom")
            return ["ABC"]

        with patch("main.get_new_announcements", return_value=anns), \
            patch("main.get_my_coins", return_value=["ABC"]), \
            patch("main.parse_delist_coins", side_effect=parse_side_effect), \
            patch("main.match_coins", return_value=["ABC"]), \
            patch("main.build_alert_message", return_value="msg"), \
            patch("main.send_telegram_message", return_value=True), \
            patch("main.save_processed_ids") as save_mock:
            out = main.run_once()

        self.assertEqual(out, 1)
        save_mock.assert_called_once_with(["2"])


if __name__ == "__main__":
    unittest.main()
