import json
import tempfile
import unittest
from pathlib import Path

from scanner import Announcement, _dedupe, _extract_announcement_id, _is_delist_title, _load_history, save_processed_ids


class ScannerCoreTests(unittest.TestCase):
    def test_extract_announcement_id_prefers_numeric_id(self) -> None:
        value = _extract_announcement_id(
            "https://www.gate.io/announcements/article/123456",
            "About delist ABC",
        )
        self.assertEqual(value, "123456")

    def test_extract_announcement_id_falls_back_to_slug(self) -> None:
        value = _extract_announcement_id(
            "https://www.gate.io/announcements/article/no-id",
            "关于下架 ABC/USDT 的公告",
        )
        self.assertTrue(value)




    def test_load_history_normalizes_non_string_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_path = Path(tmp) / "history.json"
            history_path.write_text('[123, "  abc  ", "", null]', encoding="utf-8")

            out = _load_history(str(history_path))

            self.assertEqual(out, {"123", "abc"})

    def test_save_processed_ids_creates_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_path = Path(tmp) / "nested" / "history.json"
            save_processed_ids(["b", "a"], path=str(history_path))

            self.assertTrue(history_path.exists())
            payload = json.loads(history_path.read_text(encoding="utf-8"))
            self.assertEqual(payload, ["a", "b"])

    def test_is_delist_title_supports_cn_en(self) -> None:
        self.assertTrue(_is_delist_title("About Delist ABC"))
        self.assertTrue(_is_delist_title("关于下架 ABC 交易对"))
        self.assertFalse(_is_delist_title("Weekly product update"))

    def test_dedupe_keeps_first_item_for_same_id(self) -> None:
        items = [
            Announcement(id="1", title="t1", url="u1", date=""),
            Announcement(id="1", title="t2", url="u2", date=""),
            Announcement(id="2", title="t3", url="u3", date=""),
        ]
        out = _dedupe(items)
        self.assertEqual([x.id for x in out], ["1", "2"])
        self.assertEqual(out[0].title, "t1")


if __name__ == "__main__":
    unittest.main()
