import unittest
import os
import uuid
import tempfile
from skills.market_sentiment_risk_alert_bridge import (
    process_sentiment_risk_and_dispatch_alert
)

class TestMarketSentimentRiskAlertBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.test_ticker = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.test_exchange = "NASDAQ"
        self.test_news = f"Market volatility spike detected for {self.test_ticker} due to unexpected economic data release."
        self.test_url = f"https://api.example.com/v1/market/risk/{uuid.uuid4().hex}"
        self.test_token = f"TOKEN_{uuid.uuid4().hex}"
        self.test_chat_id = str(uuid.uuid4().int[:8])
        
        self.temp_storage = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_storage.close()
        self.storage_file = self.temp_storage.name

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_sentiment_risk_alert_bridge_composition(self):
        min_threshold = float(uuid.uuid4().int % 50) + 1.0
        severity_level = "HIGH"
        channels = ["telegram", "webhook"]

        result = process_sentiment_risk_and_dispatch_alert(
            ticker=self.test_ticker,
            exchange=self.test_exchange,
            news_snippet=self.test_news,
            url=self.test_url,
            telegram_token=self.test_token,
            chat_id=self.test_chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )

        self.assertIsInstance(result, dict)
        self.assertIn("risk_evaluation", result)
        self.assertIn("dispatch_status", result)
        
        risk_data = result["risk_evaluation"]
        self.assertIsNotNone(risk_data)

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Интеграционный модуль должен задействовать хранилище через market_portfolio_alert_dispatcher"
        )

if __name__ == "__main__":
    unittest.main()