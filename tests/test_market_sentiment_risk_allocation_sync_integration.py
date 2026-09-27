import unittest
import os
import uuid
import tempfile
from skills.market_sentiment_risk_allocation_sync import (
    process_sentiment_risk_allocation_sync
)
from skills.market_sentiment_risk_alert_bridge import MarketSentimentRiskAlertBridge
from skills.market_portfolio_alert_dispatcher import send_telegram_notification

class TestMarketSentimentRiskAllocationSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.exchange = "NASDAQ"
        self.news_snippet = f"Critical market crash warning generated at {uuid.uuid4()}"
        self.url = f"https://example.com/news/{uuid.uuid4()}"
        self.telegram_token = f"TOKEN_{uuid.uuid4().hex}"
        self.chat_id = f"CHAT_{uuid.uuid4().hex[:6]}"
        self.severity_level = "HIGH"
        self.min_threshold = 0.75
        self.channels = ["telegram", "storage"]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_sentiment_risk_allocation_sync_end_to_end(self):
        result = process_sentiment_risk_allocation_sync(
            ticker=self.ticker,
            exchange=self.exchange,
            news_snippet=self.news_snippet,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("ticker", result)
        self.assertEqual(result["ticker"], self.ticker)

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Интеграционный модуль должен создать или обновить файл хранилища для перебалансировки портфеля."
        )

        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertTrue(len(content) > 0, "Файл хранилища не должен быть пустым.")
            self.assertIn(self.ticker, content)

    def test_composition_with_required_skills(self):
        bridge = MarketSentimentRiskAlertBridge(
            token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertIsNotNone(bridge, "Компонент market_sentiment_risk_alert_bridge должен успешно инициализироваться.")
        self.assertTrue(callable(send_telegram_notification), "Компонент market_portfolio_alert_dispatcher должен предоставлять функцию отправки.")

        sync_result = process_sentiment_risk_allocation_sync(
            ticker=self.ticker,
            exchange=self.exchange,
            news_snippet=self.news_snippet,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertEqual(sync_result.get("ticker"), self.ticker)

if __name__ == "__main__":
    unittest.main()