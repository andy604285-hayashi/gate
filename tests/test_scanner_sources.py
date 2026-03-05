import unittest
from unittest.mock import patch

from scanner import Announcement, _parse_api_announcements, _parse_rss_announcements, scan_announcements


class ScannerSourceParsingTests(unittest.TestCase):
    def test_parse_api_announcements_from_dict_data(self) -> None:
        payload = {
            "data": [
                {
                    "title": "Gate will delist ABC",
                    "url": "https://www.gate.io/announcements/123456",
                    "date": "2026-01-01",
                },
                {
                    "title": "Weekly update",
                    "url": "https://www.gate.io/announcements/999999",
                },
            ]
        }
        out = _parse_api_announcements(payload)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].id, "123456")

    def test_parse_rss_announcements_filters_keywords(self) -> None:
        xml = """
        <rss><channel>
          <item>
            <title>About delist XYZ/USDT</title>
            <link>https://www.gate.io/announcements/234567</link>
            <pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate>
          </item>
          <item>
            <title>Regular maintenance notice</title>
            <link>https://www.gate.io/announcements/345678</link>
          </item>
        </channel></rss>
        """
        out = _parse_rss_announcements(xml)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].id, "234567")


class ScannerSourceMergeTests(unittest.TestCase):
    def test_scan_announcements_merges_multi_sources(self) -> None:
        api_items = [
            Announcement(id="1", title="t1", url="u1", date=""),
            Announcement(id="2", title="t2", url="u2", date=""),
        ]
        web_items = [Announcement(id="2", title="t2-new", url="u2-new", date="")]
        rss_items = [Announcement(id="3", title="t3", url="u3", date="")]

        with (
            patch("scanner._fetch_from_api", return_value=api_items),
            patch("scanner._fetch_from_web", return_value=web_items),
            patch("scanner._fetch_from_rss", return_value=rss_items),
        ):
            out = scan_announcements()

        self.assertEqual([x.id for x in out], ["1", "2", "3"])
        self.assertEqual(out[1].title, "t2")

    def test_scan_announcements_works_when_one_source_fails(self) -> None:
        with (
            patch("scanner._fetch_from_api", side_effect=RuntimeError("boom")),
            patch("scanner._fetch_from_web", return_value=[]),
            patch(
                "scanner._fetch_from_rss",
                return_value=[Announcement(id="9", title="t9", url="u9", date="")],
            ),
        ):
            out = scan_announcements()

        self.assertEqual([x.id for x in out], ["9"])


if __name__ == "__main__":
    unittest.main()
