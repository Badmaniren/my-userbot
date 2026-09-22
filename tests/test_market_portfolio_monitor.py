import os
import unittest
from unittest.mock import patch
from skills.market_portfolio_monitor import (
    MarketPortfolioMonitor,
    MarketMonitorException,
    start_new
)


class TestMarketPortfolioMonitor(unittest.TestCase):
    def setUp(self):
        self.test_storage = "test_monitor_unit.db"

    def tearDown(self):
        if os.path.exists(self.test_storage):
            try:
                os.remove(self.test_storage)
            except OSError:
                pass

    def test_init_invalid_storage(self):
        with self.assertRaises(MarketMonitorException):
            MarketPortfolioMonitor(storage_file="")
        with self.assertRaises(MarketMonitorException):
            MarketPortfolioMonitor(storage_file=None)

    @patch("skills.db_storage.MarketParser.fetch_price")
    @patch("skills.db_storage.MarketParser.fetch_and_store")
    def test_fetch_and_process_market_data_success(self, mock_store, mock_fetch):
        mock_fetch.return_value = {"price": 150.5}
        monitor = MarketPortfolioMonitor(storage_file=self.test_storage)
        price = monitor.fetch_and_process_market_data("AAPL", "http://example.com/api")
        self.assertEqual(price, 150.5)

    def test_fetch_and_process_market_data_invalid_inputs(self):
        monitor = MarketPortfolioMonitor(storage_file=self.test_storage)
        with self.assertRaises(MarketMonitorException):
            monitor.fetch_and_process_market_data("", "http://example.com")
        with self.assertRaises(MarketMonitorException):
            monitor.fetch_and_process_market_data("AAPL", "")

    def test_track_insider_trades_success(self):
        monitor = MarketPortfolioMonitor(storage_file=self.test_storage)
        trade = {
            "symbol": "TSLA",
            "volume": 15000,
            "insider_name": "Elon Musk",
            "trade_type": "BUY"
        }
        res = monitor.track_insider_trades(trade)
        self.assertEqual(res["symbol"], "TSLA")
        self.assertEqual(res["volume"], 15000.0)
        self.assertTrue(res["is_suspicious"])

    def test_track_insider_trades_invalid_data(self):
        monitor = MarketPortfolioMonitor(storage_file=self.test_storage)
        with self.assertRaises(MarketMonitorException):
            monitor.track_insider_trades("not a dict")
        with self.assertRaises(MarketMonitorException):
            monitor.track_insider_trades({"symbol": "AAPL", "volume": 100})  # Missing insider_name

    def test_scan_insider_activity(self):
        monitor = MarketPortfolioMonitor(storage_file=self.test_storage)
        trade = {
            "symbol": "AAPL",
            "volume": 5000,
            "insider_name": "Tim Cook",
            "trade_type": "BUY"
        }
        monitor.track_insider_trades(trade)
        res = monitor.scan_insider_activity("AAPL")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["symbol"], "AAPL")

    @patch("skills.market_portfolio_monitor.MarketPortfolioMonitor.fetch_and_process_market_data")
    @patch("skills.market_portfolio_telegram_notifier.send_telegram_notification")
    def test_run_pipeline_and_start_new(self, mock_notify, mock_fetch):
        mock_fetch.return_value = 200.0
        res = start_new("BTC", "http://crypto.com", "token123", "chat456", self.test_storage)
        self.assertTrue(res)
        mock_fetch.assert_called_once_with("BTC", "http://crypto.com")
        mock_notify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
