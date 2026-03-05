import json
import os
import tempfile
import unittest
from pathlib import Path

from config import SETTINGS
from tools import preflight_check


class PreflightCheckTests(unittest.TestCase):
    def test_check_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            watch = Path(tmp) / "watch.json"
            hist = Path(tmp) / "history.json"
            watch.write_text("[]", encoding="utf-8")
            hist.write_text("[]", encoding="utf-8")

            old_watch, old_hist = SETTINGS.watchlist_file, SETTINGS.history_file
            try:
                object.__setattr__(SETTINGS, "watchlist_file", str(watch))
                object.__setattr__(SETTINGS, "history_file", str(hist))
                rows = preflight_check.check_required_files()
            finally:
                object.__setattr__(SETTINGS, "watchlist_file", old_watch)
                object.__setattr__(SETTINGS, "history_file", old_hist)

            self.assertTrue(all(ok for _, ok, _ in rows))

    def test_check_env_hints(self) -> None:
        old = {k: os.environ.get(k) for k in ["TG_BOT_TOKEN", "TG_CHAT_ID", "GATE_API_KEY", "GATE_API_SECRET"]}
        try:
            for k in old:
                os.environ.pop(k, None)
            rows = preflight_check.check_env_hints()
            self.assertEqual(len(rows), 2)
            self.assertFalse(rows[0][1])
            self.assertFalse(rows[1][1])
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_collect_preflight_report_shape(self) -> None:
        report = preflight_check.collect_preflight_report()
        self.assertIn("status", report)
        self.assertIn("groups", report)
        self.assertIn("required_files", report["groups"])

    def test_check_writable_paths_includes_heartbeat_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history = Path(tmp) / "history.json"
            heartbeat = Path(tmp) / "hb" / "heartbeat.json"

            old_history = SETTINGS.history_file
            old_heartbeat = SETTINGS.heartbeat_file
            try:
                object.__setattr__(SETTINGS, "history_file", str(history))
                object.__setattr__(SETTINGS, "heartbeat_file", str(heartbeat))
                rows = preflight_check.check_writable_paths()
            finally:
                object.__setattr__(SETTINGS, "history_file", old_history)
                object.__setattr__(SETTINGS, "heartbeat_file", old_heartbeat)

            row_map = {key: (ok, msg) for key, ok, msg in rows}
            self.assertIn(str(history), row_map)
            self.assertIn(str(heartbeat), row_map)
            self.assertTrue(row_map[str(heartbeat)][0])
            self.assertTrue(heartbeat.exists())

    def test_run_preflight_json_output(self) -> None:
        from io import StringIO
        import contextlib

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            code = preflight_check.run_preflight(json_output=True)
        self.assertIn(code, (0, 1))
        payload = json.loads(buf.getvalue())
        self.assertIn("status", payload)

if __name__ == "__main__":
    unittest.main()
