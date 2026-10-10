import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.request_id = f"req-{uuid.uuid4()}"
        self.symbol = random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT", "AAPL", "TSLA"])
        self.percentage = round(random.uniform(5.0, 35.0), 2)
        self.shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(random.randint(2, 5))]
        self.storage_file = f"test_stress_pipeline_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_auto_hedge_sync_real_integration(self):
        sync_module = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )

        result = sync_module.synchronize(
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
        self.assertIsNotNone(stress_res)

    def test_run_auto_hedge_sync_helper_function(self):
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
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertIn("advisor_recommendation", result)
        self.assertIn("stress_pipeline_result", result)


if __name__ == "__main__":
    unittest.main()