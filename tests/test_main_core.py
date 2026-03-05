import unittest
from argparse import Namespace
from unittest.mock import patch

import main
from scanner import Announcement


class MainCoreTests(unittest.TestCase):
    def test_run_once_no_announcements(self) -> None:
        with patch("main.get_new_announcements", return_value=[]), patch("main.write_heartbeat") as hb_mock:
            out = main.run_once()
        self.assertEqual(out, 0)
        hb_mock.assert_called_once_with(status="idle", processed=0)

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
            patch("main.save_processed_ids") as save_mock, \
            patch("main.write_heartbeat") as hb_mock:
            out = main.run_once()

        self.assertEqual(out, 2)
        self.assertEqual(save_mock.call_count, 2)
        hb_mock.assert_called_once_with(status="ok", processed=2)

    def test_run_once_dry_run_skips_send_and_history(self) -> None:
        anns = [Announcement(id="1", title="t1", url="u1", date="")]
        with patch("main.get_new_announcements", return_value=anns), \
            patch("main.get_my_coins", return_value=["ABC"]), \
            patch("main.parse_delist_coins", return_value=["ABC"]), \
            patch("main.match_coins", return_value=["ABC"]), \
            patch("main.build_alert_message", return_value="msg"), \
            patch("main.send_telegram_message") as send_mock, \
            patch("main.save_processed_ids") as save_mock, \
            patch("main.write_heartbeat") as hb_mock:
            out = main.run_once(dry_run=True)

        self.assertEqual(out, 1)
        send_mock.assert_not_called()
        save_mock.assert_not_called()
        hb_mock.assert_called_once_with(status="ok", processed=1)

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
            patch("main.save_processed_ids") as save_mock, \
            patch("main.write_heartbeat") as hb_mock:
            out = main.run_once()

        self.assertEqual(out, 1)
        save_mock.assert_called_once_with(["2"])
        hb_mock.assert_called_once_with(status="ok", processed=1)

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

    def test_arg_parser_supports_dry_run(self) -> None:
        args = main.build_arg_parser().parse_args(["--once", "--dry-run"])
        self.assertTrue(args.once)
        self.assertTrue(args.dry_run)

    def test_arg_parser_supports_once_json(self) -> None:
        args = main.build_arg_parser().parse_args(["--once", "--once-json"])
        self.assertTrue(args.once)
        self.assertTrue(args.once_json)

    def test_arg_parser_supports_max_cycles(self) -> None:
        args = main.build_arg_parser().parse_args(["--max-cycles", "3"])
        self.assertEqual(args.max_cycles, 3)

    def test_arg_parser_rejects_negative_max_cycles(self) -> None:
        with self.assertRaises(SystemExit):
            main.build_arg_parser().parse_args(["--max-cycles", "-1"])

    def test_status_mode_exits_without_run_loop(self) -> None:
        ns = Namespace(
            once=False,
            log_level="INFO",
            preflight=False,
            preflight_json=False,
            status=True,
            status_json=False,
            dry_run=False,
            once_json=False,
            max_cycles=0,
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

    def test_run_loop_writes_error_heartbeat_on_exception(self) -> None:
        with patch("main.run_once", side_effect=RuntimeError("loop boom")), \
            patch("main.time.sleep"), \
            patch("main.write_heartbeat") as hb_mock:
            main.run_loop(max_cycles=1)

        hb_mock.assert_called_once()
        self.assertEqual(hb_mock.call_args.kwargs["status"], "error")

    def test_main_forwards_max_cycles_to_run_loop(self) -> None:
        ns = Namespace(
            once=False,
            log_level="INFO",
            preflight=False,
            preflight_json=False,
            status=False,
            status_json=False,
            dry_run=True,
            once_json=False,
            max_cycles=2,
        )
        with (
            patch("main.build_arg_parser") as parser_mock,
            patch("main.setup_logging"),
            patch("main.run_loop") as run_loop_mock,
        ):
            parser_mock.return_value.parse_args.return_value = ns
            main.main()

        run_loop_mock.assert_called_once_with(max_cycles=2, dry_run=True)

    def test_main_warns_once_json_without_once(self) -> None:
        ns = Namespace(
            once=False,
            log_level="INFO",
            preflight=False,
            preflight_json=False,
            status=False,
            status_json=False,
            dry_run=False,
            once_json=True,
            max_cycles=1,
        )
        with (
            patch("main.build_arg_parser") as parser_mock,
            patch("main.setup_logging"),
            patch("main.logger.warning") as warn_mock,
            patch("main.run_loop"),
        ):
            parser_mock.return_value.parse_args.return_value = ns
            main.main()

        warn_mock.assert_any_call("--once-json is ignored unless --once is set")

    def test_main_warns_status_json_without_status(self) -> None:
        ns = Namespace(
            once=False,
            log_level="INFO",
            preflight=False,
            preflight_json=False,
            status=False,
            status_json=True,
            dry_run=False,
            once_json=False,
            max_cycles=1,
        )
        with (
            patch("main.build_arg_parser") as parser_mock,
            patch("main.setup_logging"),
            patch("main.logger.warning") as warn_mock,
            patch("main.run_loop"),
        ):
            parser_mock.return_value.parse_args.return_value = ns
            main.main()

        warn_mock.assert_any_call("--status-json is ignored unless --status is set")


if __name__ == "__main__":
    unittest.main()
