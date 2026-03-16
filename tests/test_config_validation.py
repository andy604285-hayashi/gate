import unittest

from config import Settings


class ConfigValidationTests(unittest.TestCase):
    def test_warns_on_partial_gate_credentials(self) -> None:
        s = Settings(gate_api_key="key", gate_api_secret="", telegram_bot_token="", telegram_chat_id="")
        warnings = s.validation_warnings()
        self.assertTrue(any("GATE_API_KEY" in w for w in warnings))

    def test_warns_on_partial_telegram_credentials(self) -> None:
        s = Settings(gate_api_key="", gate_api_secret="", telegram_bot_token="tok", telegram_chat_id="")
        warnings = s.validation_warnings()
        self.assertTrue(any("TG_BOT_TOKEN" in w for w in warnings))

    def test_warns_on_non_positive_poll_interval(self) -> None:
        s = Settings(poll_interval_seconds=0)
        warnings = s.validation_warnings()
        self.assertTrue(any("POLL_INTERVAL_SECONDS" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
