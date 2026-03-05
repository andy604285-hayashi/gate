import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import matcher
from config import SETTINGS


class MatcherCoreTests(unittest.TestCase):
    def test_get_my_coins_fallback_when_api_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            watchlist_path = Path(tmp) / "watchlist.json"
            watchlist_path.write_text(json.dumps(["abc", "XYZ"]), encoding="utf-8")

            old_watchlist = SETTINGS.watchlist_file
            try:
                object.__setattr__(SETTINGS, "watchlist_file", str(watchlist_path))
                with patch("matcher._fetch_spot_balances", side_effect=matcher.requests.RequestException("boom")):
                    coins = matcher.get_my_coins()
                self.assertEqual(coins, ["ABC", "XYZ"])
            finally:
                object.__setattr__(SETTINGS, "watchlist_file", old_watchlist)

    def test_load_watchlist_invalid_json_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            watchlist_path = Path(tmp) / "watchlist.json"
            watchlist_path.write_text("{oops", encoding="utf-8")

            old_watchlist = SETTINGS.watchlist_file
            try:
                object.__setattr__(SETTINGS, "watchlist_file", str(watchlist_path))
                self.assertEqual(matcher._load_watchlist(), [])
            finally:
                object.__setattr__(SETTINGS, "watchlist_file", old_watchlist)

    def test_match_coins_intersection(self) -> None:
        out = matcher.match_coins(["abc", "BTC", "XRP"], ["ABC", "ETH", "XRP"])
        self.assertEqual(out, ["ABC", "XRP"])


if __name__ == "__main__":
    unittest.main()
