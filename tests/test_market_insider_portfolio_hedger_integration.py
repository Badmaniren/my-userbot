import unittest
import uuid
import random
import os
from skills.market_insider_portfolio_hedger import (
    DbStorage,
    MarketInsiderActivityTracker,
    MarketAnomalyDetector,
    MarketPortfolioMonitor,
    MarketPortfolioStrategyOptimizer,
    MarketInsiderPortfolioHedger,
    start_new
)

class TestMarketInsiderPortfolioHedgerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_hedge_{uuid.uuid4().hex}.db"
        self.connection_string = f"sqlite:///{self.db_path}"
        self.portfolio_id = uuid.uuid4().hex
        self.ticker = f"TICK_{random.randint(1000, 9999)}"
        self.volume = random.randint(100, 5000)

        self.db_storage = DbStorage(self.connection_string)
        self.tracker = MarketInsiderActivityTracker(self.db_storage)
        self.detector = MarketAnomalyDetector()
        self.monitor = MarketPortfolioMonitor(self.db_storage)
        self.optimizer = MarketPortfolioStrategyOptimizer()

        self.hedger = MarketInsiderPortfolioHedger(
            db_storage=self.db_storage,
            tracker=self.tracker,
            detector=self.detector,
            monitor=self.monitor,
            optimizer=self.optimizer
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_end_to_end_hedge_workflow(self):
        initial_val = round(random.uniform(10000.0, 500000.0), 2)
        self.monitor.register_portfolio(self.portfolio_id, initial_val)

        self.tracker.record_insider_activity(self.ticker, self.volume, "BUY")

        anomaly_res = self.detector.scan_for_anomalies(self.ticker)
        self.assertIsNotNone(anomaly_res)
        self.assertEqual(anomaly_res["ticker"], self.ticker)

        hedge_result = self.hedger.execute_hedge_routine(
            portfolio_id=self.portfolio_id,
            target_ticker=self.ticker,
            anomaly_signal_id=anomaly_res["signal_id"]
        )

        self.assertEqual(hedge_result["hedge_status"], "EXECUTED")
        self.assertEqual(hedge_result["portfolio_id"], self.portfolio_id)
        self.assertEqual(hedge_result["ticker"], self.ticker)
        self.assertEqual(hedge_result["signal_id"], anomaly_res["signal_id"])

        state = self.db_storage.get_portfolio_hedge_state(self.portfolio_id)
        self.assertIsNotNone(state)
        self.assertEqual(state["last_hedged_ticker"], self.ticker)

    def test_start_new_compatibility_wrapper(self):
        class MockDetector:
            def detect(self):
                return {"anomaly_id": uuid.uuid4().hex}

        class MockParser:
            def parse(self):
                return True

        mock_detector = MockDetector()
        mock_parser = MockParser()

        res = start_new(
            portfolio_id=self.portfolio_id,
            db_storage=self.db_storage,
            market_anomaly_detector=mock_detector,
            market_parser=mock_parser
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertIsNotNone(res["anomaly_id"])

if __name__ == "__main__":
    unittest.main()