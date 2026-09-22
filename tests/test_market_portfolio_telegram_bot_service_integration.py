import unittest
import os
import uuid
import random
from skills.market_portfolio_telegram_bot_service import *

class TestMarketPortfolioTelegramBotServiceIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        self.url = f"https://example.com/api/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_telegram_bot_service_pipeline_integration(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        self.assertTrue(os.path.exists(self.storage_file))

        valuation = PortfolioValuation(self.storage_file)
        summary = valuation.get_total_summary(self.url)
        self.assertIsNotNone(summary)

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)
        self.assertIsInstance(metrics, dict)

        command_result = start_new(self.telegram_token, self.chat_id, f"Portfolio report for {self.symbol}")
        self.assertIn(command_errored := type(command_result), [bool, type(None)])

        event_logger = MarketPortfolioWebhookEventLogger(self.storage_file, self.url)
        event_logger.log_and_sync_event(self.symbol, self.price, self.url, [random.randint(1, 5)])
        stream = event_logger.get_event_stream()
        self.assertIsNotNone(stream)

if __name__ == '__main__':
    unittest.main()