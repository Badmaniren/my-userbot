import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"stress_storage_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_auto_hedge_sync_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        symbol = random.choice(["BTC", "ETH", "SPY", "QQQ", "AAPL"])
        percentage = round(random.uniform(5.0, 35.0), 2)
        shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(1, 3))]

        syncer = MarketPortfolioStressAutoHedgeSync(
            db_storage=None,
            monitor=None,
            evaluator=None,
            rebalancer=None,
            storage_file=self.storage_file
        )

        result = syncer.synchronize(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("request_id"), request_id)
        
        advisor_rec = result.get("advisor_recommendation")
        self.assertIsInstance(advisor_rec, dict)
        self.assertEqual(advisor_rec.get("portfolio_id"), portfolio_id)

        pipeline_res = result.get("stress_pipeline_result")
        self.assertIsNotNone(pipeline_res)

        run_result = run_auto_hedge_sync(
            db_storage=None,
            monitor=None,
            evaluator=None,
            rebalancer=None,
            storage_file=self.storage_file,
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.assertIsInstance(run_result, dict)
        self.assertEqual(run_result.get("status"), "success")
        self.assertEqual(run_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(run_result.get("request_id"), request_id)


if __name__ == "__main__":
    unittest.main()