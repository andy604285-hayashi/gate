import unittest
from argparse import Namespace
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

    def test_arg_parser_supports_preflight(self) -> None:
        args = main.build_arg_parser().parse_args(["--preflight"])
        self.assertTrue(args.preflight)

    def test_arg_parser_supports_preflight_json(self) -> None:
        args = main.build_arg_parser().parse_args(["--preflight", "--preflight-json"])
        self.assertTrue(args.preflight)
        self.assertTrue(args.preflight_json)

    def test_arg_parser_supports_status(self) -> None:
        args = main.build_arg_parser().parse_args(["--status"])
        self.assertTrue(args.status)

    def test_arg_parser_supports_status_json(self) -> None:
        args = main.build_arg_parser().parse_args(["--status", "--status-json"])
        self.assertTrue(args.status)
        self.assertTrue(args.status_json)

    def test_status_mode_exits_without_run_loop(self) -> None:
        ns = Namespace(
            once=False,
            log_level="INFO",
            preflight=False,
            preflight_json=False,
            status=True,
            status_json=False,
        )
        with patch("main.build_arg_parser") as parser_mock, \
            patch("main.setup_logging"), \
            patch("main.print_status") as status_mock, \
            patch("main.run_loop") as run_loop_mock, \
            patch("main.run_once") as run_once_mock:
            parser_mock.return_value.parse_args.return_value = ns
            main.main()

        status_mock.assert_called_once_with(json_output=False)
        run_loop_mock.assert_not_called()
        run_once_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
