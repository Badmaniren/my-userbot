import os
import json
import unittest
from skills.market_portfolio_monitor import (
    MarketPortfolioMonitor,
    run_pipeline
)


class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_storage = "test_monitor_integration.db"

    def tearDown(self):
        if os.path.exists(self.test_storage):
            try:
                os.remove(self.test_storage)
            except OSError:
                pass

    def test_full_pipeline_execution(self):
        result = run_pipeline(
            symbol="AAPL",
            url="http://mock-market-data.local/aapl",
            telegram_token="dummy_token",
            chat_id="dummy_chat_id",
            storage_file=self.test_storage
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_storage))

    def test_insider_tracking_integration(self):
        monitor = MarketPortfolioMonitor(storage_file=self.test_storage)
        trade = {
            "symbol": "MSFT",
            "volume": 25000,
            "insider_name": "Satya Nadella",
            "trade_type": "SELL"
        }
        res = monitor.track_insider_trades(trade)
        self.assertTrue(res["is_suspicious"])

        records = monitor.scan_insider_activity("MSFT")
        self.assertTrue(len(records) > 0)


if __name__ == "__main__":
    unittest.main()
