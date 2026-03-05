import unittest

from scanner import _parse_api_announcements, _parse_rss_announcements


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


if __name__ == "__main__":
    unittest.main()
