import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync

class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.symbol = random.choice(["BTC/USD", "ETH/USD", "SPY", "QQQ", "GLD"])
        self.percentage = round(random.uniform(1.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.15, 0.15), 4) for _ in range(3)]
        self.storage_file = f"test_stress_pipeline_{uuid.uuid4().hex[:6]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_synchronize_integration_real_execution(self):
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

        advisor_rec = result.get("advisor_recommendation")
        self.assertIsInstance(advisor_rec, dict)
        self.assertEqual(advisor_rec.get("portfolio_id"), self.portfolio_id)

        stress_res = result.get("stress_pipeline_result")
        self.assertIsInstance(stress_res, dict)

    def test_run_auto_hedge_sync_wrapper(self):
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
        self.assertIn("advisor_recommendation", result)
        self.assertIn("stress_pipeline_result", result)

if __name__ == "__main__":
    unittest.main()