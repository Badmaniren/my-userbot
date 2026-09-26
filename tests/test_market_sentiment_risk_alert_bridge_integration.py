import unittest
import uuid
import random
import os
from skills.market_sentiment_risk_alert_bridge import (
    MarketSentimentRiskAlertBridge,
    process_sentiment_risk_and_dispatch_alert
)

class TestMarketSentimentRiskAlertBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.token = f"test_token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        
        self.tickers = ["AAPL", "TSLA", "BTC", "ETH", "GOOGL", "MSFT"]
        self.exchanges = ["NASDAQ", "NYSE", "BINANCE", "COINBASE"]
        self.news_snippets = [
            "Market shows extreme volatility amid regulatory updates.",
            "Bullish momentum continues as trading volume surges.",
            "Unexpected supply chain disruptions impact short-term outlook.",
            "Macroeconomic indicators point towards a potential correction."
        ]
        self.urls = [
            f"https://example.com/news/{uuid.uuid4().hex[:6]}"
            for _ in range(4)
        ]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_evaluate_and_dispatch_integration(self):
        random_ticker = random.choice(self.tickers)
        random_exchange = random.choice(self.exchanges)
        random_snippet = random.choice(self.news_snippets)
        random_url = random.choice(self.urls)
        
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        random_severity = random.choice(severity_levels)
        random_threshold = round(random.uniform(0.1, 0.9), 2)

        bridge = MarketSentimentRiskAlertBridge(
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        result = bridge.bridge_evaluate_and_dispatch(
            ticker=random_ticker,
            exchange=random_exchange,
            news_snippet=random_snippet,
            url=random_url,
            severity_level=random_severity,
            min_threshold=random_threshold,
            channels=["telegram"]
        )

        self.assertIsInstance(result, dict)
        self.assertIn("risk_data", result)
        self.assertIn("dispatch_result", result)

    def test_process_sentiment_risk_and_dispatch_alert_wrapper(self):
        random_ticker = random.choice(self.tickers)
        random_exchange = random.choice(self.exchanges)
        random_snippet = random.choice(self.news_snippets)
        random_url = random.choice(self.urls)

        wrapper_result = process_sentiment_risk_and_dispatch_alert(
            ticker=random_ticker,
            exchange=random_exchange,
            news_snippet=random_snippet,
            url=random_url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="HIGH",
            min_threshold=0.4,
            channels=["telegram"]
        )

        self.assertIsInstance(wrapper_result, dict)
        self.assertIn("risk_evaluation", wrapper_result)
        self.assertIn("dispatch_status", wrapper_result)

    def test_bridge_process_stream_integration(self):
        random_stream_source = [f"stream_item_{uuid.uuid4().hex[:6]}" for _ in range(3)]
        
        bridge = MarketSentimentRiskAlertBridge(
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        stream_results = bridge.bridge_process_stream(random_stream_source)
        self.assertIsInstance(stream_results, list)

if __name__ == "__main__":
    unittest.main()