import unittest
from unittest.mock import patch

from notifier import _fit_telegram_text, build_alert_message, send_telegram_message
from scanner import Announcement


class NotifierCoreTests(unittest.TestCase):
    def test_build_alert_message_contains_sections(self) -> None:
        ann = Announcement(id="1", title="关于下架 ABC 的公告", url="https://x", date="")
        msg = build_alert_message(ann, ["ABC", "XYZ"], ["ABC"])
        self.assertIn("Gate.io 下架警报", msg)
        self.assertIn("ABC", msg)
        self.assertIn("XYZ", msg)
        self.assertIn("建议尽快", msg)

    def test_fit_telegram_text_truncates_long_text(self) -> None:
        text = "A" * 5000
        out = _fit_telegram_text(text, limit=100)
        self.assertLessEqual(len(out), 100)
        self.assertTrue(out.endswith("...[truncated]"))

    def test_send_telegram_message_succeeds_on_retry(self) -> None:
        bad = Exception("network")
        with patch("notifier._telegram_send_once", side_effect=[bad, True]):
            with patch("notifier.requests.RequestException", Exception):
                out = send_telegram_message("hello", retries=2, backoff_seconds=0)
        self.assertTrue(out)

    def test_send_telegram_message_returns_false_when_all_fail(self) -> None:
        with patch("notifier._telegram_send_once", return_value=False):
            out = send_telegram_message("hello", retries=1, backoff_seconds=0)
        self.assertFalse(out)

    def test_send_telegram_message_sends_truncated_text(self) -> None:
        with patch("notifier._telegram_send_once", return_value=True) as send_mock:
            out = send_telegram_message("B" * 5000, retries=0, backoff_seconds=0)
        self.assertTrue(out)
        sent_text = send_mock.call_args[0][0]
        self.assertLessEqual(len(sent_text), 4096)


if __name__ == "__main__":
    unittest.main()
