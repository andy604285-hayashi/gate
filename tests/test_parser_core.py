import unittest

from parser import extract_symbols_from_text


class ParserCoreTests(unittest.TestCase):
    def test_extract_pair_symbols(self) -> None:
        text = "Gate.io will delist ABC/USDT and XYZ_USDT pairs"
        out = extract_symbols_from_text(text)
        self.assertIn("ABC", out)
        self.assertIn("XYZ", out)

    def test_drop_common_non_symbol_words(self) -> None:
        text = "Announcement: token pairs will be removed on Gate"
        out = extract_symbols_from_text(text)
        self.assertNotIn("ANNOUNCEMENT", out)
        self.assertNotIn("TOKEN", out)
        self.assertNotIn("PAIR", out)
        self.assertNotIn("GATE", out)

    def test_keep_real_symbols_from_mixed_text(self) -> None:
        text = "关于下架 MEME1, ABC2 交易对及 DEF/USDT"
        out = extract_symbols_from_text(text)
        self.assertIn("MEME1", out)
        self.assertIn("ABC2", out)
        self.assertIn("DEF", out)


if __name__ == "__main__":
    unittest.main()
