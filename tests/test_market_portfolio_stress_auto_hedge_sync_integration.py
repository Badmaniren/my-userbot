import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.request_id = f"req-{uuid.uuid4()}"
        self.symbol = random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT", "AAPL", "TSLA"])
        self.percentage = round(random.uniform(5.0, 30.0), 2)
        self.shifts = random.randint(1, 10)
        self.storage_file = f"test_stress_storage_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_auto_hedge_sync_integration_flow(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )

        result = syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)

        self.assertIn("advisor_recommendation", result)
        self.assertIn("stress_pipeline_result", result)

    def test_run_auto_hedge_sync_wrapper_integration(self):
        result = run_auto_hedge_sync(
            db_storage=None,
            monitor=None,
            evaluator=None,
            rebalancer=None,
            storage_file=self.storage_file,
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)


if __name__ == "__main__":
    unittest.main()