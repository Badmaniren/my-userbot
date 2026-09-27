import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import tempfile
import sqlite3

from skills.market_insider_portfolio_hedger import (
    start_new,
    DbStorage,
    MarketInsiderActivityTracker,
    MarketAnomalyDetector,
    MarketPortfolioMonitor,
    MarketPortfolioStrategyOptimizer,
    MarketInsiderPortfolioHedger
)


class TestMarketInsiderPortfolioHedger(unittest.TestCase):

    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.portfolio_id = f"port_{self.rand_prefix}_{uuid.uuid4().hex[:6]}"
        self.ticker = f"TICK_{random.choice(['AAPL', 'TSLA', 'GOOG', 'AMZN', 'BTC'])}"
        self.anomaly_id = f"anom_{uuid.uuid4().hex}"

        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.connection_string = f"sqlite://{self.db_path}"

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_start_new_function_basic_flow(self):
        mock_db = MagicMock()
        mock_db.save = MagicMock(return_value=True)

        mock_detector = MagicMock()
        mock_detector.detect = MagicMock(return_value={"anomaly_id": self.anomaly_id})

        mock_parser = MagicMock()
        mock_parser.parse = MagicMock(return_value=True)

        result = start_new(
            portfolio_id=self.portfolio_id,
            db_storage=mock_db,
            market_anomaly_detector=mock_detector,
            market_parser=mock_parser
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("anomaly_id"), self.anomaly_id)

        mock_detector.detect.assert_called_once()
        mock_parser.parse.assert_called_once()
        mock_db.save.assert_called_once_with(portfolio_id=self.portfolio_id, anomaly_id=self.anomaly_id)

    def test_start_new_function_no_args(self):
        result = start_new()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertIsNotNone(result.get("portfolio_id"))
        self.assertIsNone(result.get("anomaly_id"))

    def test_db_storage_operations(self):
        storage = DbStorage(self.connection_string)

        initial_state = storage.get_portfolio_hedge_state(self.portfolio_id)
        self.assertIsNone(initial_state)

        storage.save_portfolio_hedge_state(self.portfolio_id, self.ticker)

        state = storage.get_portfolio_hedge_state(self.portfolio_id)
        self.assertIsNotNone(state)
        self.assertEqual(state.get("last_hedged_ticker"), self.ticker)

        # Test record activity method existence
        try:
            storage.record_activity(self.ticker, random.randint(100, 5000), "BUY")
        except Exception as e:
            self.fail(f"record_activity raised unexpected exception: {e}")

    def test_market_insider_activity_tracker(self):
        mock_storage = MagicMock()
        tracker = MarketInsiderActivityTracker(mock_storage)

        volume = random.randint(500, 15000)
        tx_type = random.choice(["BUY", "SELL"])

        tracker.record_insider_activity(self.ticker, volume, tx_type)
        mock_storage.record_activity.assert_called_once_with(self.ticker, volume, tx_type)

    def test_market_anomaly_detector(self):
        detector = MarketAnomalyDetector()
        res = detector.scan_for_anomalies(self.ticker)

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("ticker"), self.ticker)
        self.assertIn("signal_id", res)
        self.assertIn("anomaly_score", res)
        self.assertGreaterEqual(res.get("anomaly_score"), 0.0)

    def test_market_portfolio_monitor(self):
        mock_storage = MagicMock()
        monitor = MarketPortfolioMonitor(mock_storage)
        initial_value = random.uniform(10000.0, 500000.0)

        monitor.register_portfolio(self.portfolio_id, initial_value)
        self.assertIn(self.portfolio_id, monitor.portfolios)
        self.assertEqual(monitor.portfolios[self.portfolio_id], initial_value)

    def test_market_portfolio_strategy_optimizer(self):
        optimizer = MarketPortfolioStrategyOptimizer()
        try:
            res = optimizer.optimize()
            self.assertIsNone(res)
        except Exception as e:
            self.fail(f"optimize failed with exception: {e}")

    def test_market_insider_portfolio_hedger_execution(self):
        mock_db = MagicMock()
        mock_tracker = MagicMock()
        mock_detector = MagicMock()
        mock_monitor = MagicMock()
        mock_optimizer = MagicMock()

        hedger = MarketInsiderPortfolioHedger(
            db_storage=mock_db,
            tracker=mock_tracker,
            detector=mock_detector,
            monitor=mock_monitor,
            optimizer=mock_optimizer
        )

        signal_id = uuid.uuid4().hex
        exec_res = hedger.execute_hedge_routine(self.portfolio_id, self.ticker, signal_id)

        self.assertIsInstance(exec_res, dict)
        self.assertEqual(exec_res.get("hedge_status"), "EXECUTED")
        self.assertEqual(exec_res.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(exec_res.get("ticker"), self.ticker)
        self.assertEqual(exec_res.get("signal_id"), signal_id)

        mock_db.save_portfolio_hedge_state.assert_called_once_with(self.portfolio_id, self.ticker)


if __name__ == "__main__":
    unittest.main()